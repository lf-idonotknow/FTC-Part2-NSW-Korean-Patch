#!/usr/bin/env python3
"""Verify the public FTC02 GitHub release payload without external packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


EXPECTED_ROMFS_FILES = 157
TITLE_ID = "010078400f7b0000"
FORBIDDEN_NAMES = {"prod.keys", "title.keys"}
FORBIDDEN_SUFFIXES = {".nsp", ".xci", ".nca", ".tik", ".cert", ".keys"}


class VerificationError(ValueError):
    """Raised when a public release payload violates its manifest."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_manifest(root: Path) -> dict[str, object]:
    path = root / "release/release_manifest.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"릴리스 매니페스트를 읽을 수 없습니다: {path}") from exc
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or str(document.get("title_id", "")).lower() != TITLE_ID
        or int(document.get("runtime_files", -1)) != EXPECTED_ROMFS_FILES
    ):
        raise VerificationError("지원하지 않는 릴리스 매니페스트입니다.")
    return document


def verify_repository_tree(root: Path) -> None:
    forbidden: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if (
            path.name.lower() in FORBIDDEN_NAMES
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            forbidden.append(relative)
        if path.stat().st_size >= 100 * 1024 * 1024:
            forbidden.append(f"{relative} (100 MiB 이상)")
    if forbidden:
        raise VerificationError(f"공개 금지 파일이 있습니다: {forbidden}")


def verify_asset_hashes(root: Path, document: dict[str, object]) -> list[Path]:
    raw_assets = document.get("assets")
    if not isinstance(raw_assets, list) or len(raw_assets) != 1:
        raise VerificationError("릴리스 자산은 직접 설치 ZIP 1개여야 합니다.")
    assets: list[Path] = []
    for item in raw_assets:
        if not isinstance(item, dict):
            raise VerificationError("잘못된 릴리스 자산 항목이 있습니다.")
        relative = str(item.get("path", "")).replace("\\", "/")
        path = root / relative
        if (
            not relative.startswith("release/")
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not path.is_file()
        ):
            raise VerificationError(f"안전하지 않은 릴리스 자산 경로입니다: {relative}")
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if (
            actual_size != int(item.get("bytes", -1))
            or actual_hash != str(item.get("sha256", "")).upper()
        ):
            raise VerificationError(
                f"릴리스 자산 크기 또는 해시가 다릅니다: {relative}"
            )
        assets.append(path)
    return assets


def verify_checksums(root: Path, assets: list[Path]) -> None:
    expected = {
        f"{sha256_file(path)}  {path.name}"
        for path in assets
    }
    actual = {
        line.strip()
        for line in (root / "release/SHA256SUMS.txt")
        .read_text(encoding="ascii")
        .splitlines()
        if line.strip()
    }
    if actual != expected:
        raise VerificationError("SHA256SUMS.txt가 릴리스 자산과 다릅니다.")


def verify_zip_names(names: list[str], label: str) -> None:
    forbidden = [
        name
        for name in names
        if Path(name).name.lower() in FORBIDDEN_NAMES
        or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden:
        raise VerificationError(f"{label} ZIP에 공개 금지 파일이 있습니다: {forbidden}")


def verify_layeredfs_zip(path: Path, document: dict[str, object]) -> None:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        verify_zip_names(names, "LayeredFS")
        prefix = f"atmosphere/contents/{TITLE_ID}/romfs/"
        romfs_files = [
            name
            for name in names
            if name.startswith(prefix) and not name.endswith("/")
        ]
        if len(romfs_files) != EXPECTED_ROMFS_FILES:
            raise VerificationError(
                f"LayeredFS ZIP의 RomFS 파일 수가 다릅니다: {len(romfs_files)}"
            )
        if any(name.startswith("FTC02_Korean_LayeredFS/") for name in names):
            raise VerificationError("LayeredFS ZIP에 불필요한 상위 폴더가 있습니다.")
        required = {
            "README.md",
            "runtime_manifest.json",
            "manifest.sha256",
            "build_report.json",
            "licenses/OFL-1.1.txt",
            "licenses/FONT_NOTICES.md",
        }
        missing = sorted(required - set(names))
        if missing:
            raise VerificationError(f"LayeredFS ZIP 필수 파일이 없습니다: {missing}")
        runtime_manifest = archive.read("runtime_manifest.json")
    actual_runtime_hash = hashlib.sha256(runtime_manifest).hexdigest().upper()
    expected_runtime_hash = str(document["runtime_manifest_sha256"]).upper()
    if actual_runtime_hash != expected_runtime_hash:
        raise VerificationError("LayeredFS 런타임 매니페스트 해시가 다릅니다.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    document = load_manifest(root)
    if args.tag and args.tag != str(document.get("tag", "")):
        raise VerificationError(
            f"태그가 매니페스트와 다릅니다: {args.tag} != {document.get('tag')}"
        )
    verify_repository_tree(root)
    assets = verify_asset_hashes(root, document)
    verify_checksums(root, assets)
    by_name = {path.name: path for path in assets}
    verify_layeredfs_zip(
        by_name["FTC02_Korean_LayeredFS.zip"],
        document,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "tag": document["tag"],
                "assets": len(assets),
                "runtime_files": EXPECTED_ROMFS_FILES,
                "forbidden_files": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, VerificationError, zipfile.BadZipFile) as error:
        print(f"오류: {error}", file=sys.stderr)
        raise SystemExit(1)
