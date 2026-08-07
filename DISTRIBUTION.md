# GitHub 배포 절차

이 저장소의 공개 배포 파일은 `release/FTC02_Korean_LayeredFS.zip`과 `release/SHA256SUMS.txt`입니다.

## ZIP 생성

PowerShell `Compress-Archive`는 사용하지 않습니다. 반드시 저장소의 표준 도구를 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_release_zip.ps1 `
  -SourceRoot "F:\Famicon Tantei Club\FTC02_Korean_LayeredFS"
```

ZIP에는 `atmosphere/`와 `licenses/`만 들어가며, 내부 경로는 `/`를 사용해야 합니다.

## 배포 전 검사

버전, 태그, 파일 수, ZIP 크기와 SHA-256을 `release/release_manifest.json` 및 `release/SHA256SUMS.txt`에 반영한 다음 실행합니다.

```powershell
python tools\verify_release.py --tag v0.9.1
```

검사가 실패하면 커밋·태그·릴리스를 만들지 않습니다.

## GitHub 게시

1. 변경 파일을 확인하고 `main`에 커밋합니다.
2. `origin/main`으로 푸시합니다.
3. 같은 커밋에 `v0.9.1` 태그를 만들고 푸시합니다.
4. `Publish GitHub Release` Actions가 `RELEASE_NOTES.md`를 본문으로 사용해 릴리스와 첨부파일을 생성합니다.
5. Actions 완료 후 릴리스 첨부 ZIP의 크기와 SHA-256을 다시 확인합니다.
