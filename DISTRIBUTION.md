# GitHub Desktop 배포 절차

이 폴더는 이미 로컬 Git 저장소와 첫 커밋이 준비되어 있습니다.
GitHub Desktop에서 새 저장소를 다시 만들지 말고, 아래 폴더를 기존
로컬 저장소로 추가해야 합니다.

```text
F:\Famicon Tantei Club\FTC02_Korean_Patch_GitHub
```

## 1. GitHub Desktop에 로그인

1. GitHub Desktop을 실행합니다.
2. `File` → `Options` → `Accounts`를 엽니다.
3. `GitHub.com` 계정으로 로그인합니다.

## 2. 준비된 로컬 저장소 추가

1. `File` → `Add local repository...`를 누릅니다.
2. `Local path`에서 다음 폴더를 선택합니다.

   ```text
   F:\Famicon Tantei Club\FTC02_Korean_Patch_GitHub
   ```

3. `Add repository`를 누릅니다.
4. 왼쪽 변경 목록이 비어 있고 현재 브랜치가 `main`인지 확인합니다.

상위 작업 폴더인 `F:\Famicon Tantei Club`을 선택하면 NSP와 키가 있는
개발 폴더를 다루게 되므로 반드시 공개 전용 하위 폴더만 선택합니다.

## 3. GitHub에 공개 저장소로 게시

1. 상단의 `Publish repository`를 누릅니다.
2. `Name`에 원하는 저장소 이름을 입력합니다.
   권장 이름은 `FTC02-Korean-Patch`입니다.
3. 설명에는 다음처럼 입력할 수 있습니다.

   ```text
   패미컴 탐정클럽 - 뒤에 선 소녀 Nintendo Switch판 비공식 한국어 패치
   ```

4. 공개 배포라면 `Keep this code private`의 체크를 해제합니다.
5. 개인 계정에 게시하려면 `Organization`은 `None`으로 둡니다.
6. `Publish repository`를 누릅니다.
7. 완료되면 `Repository` → `View on GitHub`로 웹 저장소를 확인합니다.

## 4. 첫 GitHub Release 게시

첫 배포 후보 태그는 `v0.1.0-beta.1`입니다.

1. GitHub Desktop 왼쪽에서 `History`를 선택합니다.
2. 가장 최신 커밋을 마우스 오른쪽 버튼으로 누릅니다.
3. `Create Tag...`를 선택합니다.
4. 태그 이름에 `v0.1.0-beta.1`을 정확히 입력합니다.
5. `Create Tag`를 누릅니다.

GitHub Desktop은 기본적으로 생성한 태그를 원격 저장소에도
게시합니다. 태그가 올라가면 `Publish GitHub Release` Actions가
자동으로 실행되어 다음 두 파일을 릴리스에 첨부합니다.

- `FTC02_Korean_LayeredFS.zip`
- `SHA256SUMS.txt`

태그 이름이 `release/release_manifest.json`에 기록된 태그와 다르면
자동 게시 작업은 실패합니다.

## 5. Actions와 Release 확인

1. `Repository` → `View on GitHub`를 누릅니다.
2. 웹 페이지의 `Actions` 탭에서 다음 작업을 확인합니다.
   - `Validate release payload`
   - `Publish GitHub Release`
3. 두 작업이 녹색 체크로 끝났는지 확인합니다.
4. 저장소 메인 화면 오른쪽의 `Releases`에서
   `v0.1.0-beta.1`을 엽니다.
5. `FTC02_Korean_LayeredFS.zip`과 `SHA256SUMS.txt`가 첨부됐는지
   확인합니다.

## 6. 다음 버전 배포

1. `release\FTC02_Korean_LayeredFS.zip`을 새 검증본으로 교체합니다.
2. 다음 파일의 버전·태그·크기·SHA-256과 설명을 갱신합니다.
   - `release\release_manifest.json`
   - `release\SHA256SUMS.txt`
   - `RELEASE_NOTES.md`
3. GitHub Desktop의 `Changes`에서 변경 파일만 포함됐는지 확인합니다.
4. 왼쪽 아래 `Summary`에 변경 내용을 적고 `Commit to main`을
   누릅니다.
5. 상단의 `Push origin`을 누릅니다.
6. `History`에서 방금 만든 커밋을 오른쪽 클릭하고 새 버전 태그를
   만듭니다.

같은 태그 이름을 다시 사용하지 않습니다. 예를 들어 다음 베타는
`v0.1.0-beta.2`, 정식 후보는 `v0.1.0`처럼 올립니다.
