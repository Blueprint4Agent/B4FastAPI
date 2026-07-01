# 에이전트 가이드

이 파일을 먼저 읽고, 작업 도메인에 맞는 가이드로 이동하세요.

## 필수 읽기 순서

1. `AGENTS.md`
2. 백엔드 작업: `src/backend/BACKEND.md`
3. 프론트엔드 작업: `src/frontend/FRONTEND.md`

## 문서 동기화

구현으로 인해 동작, 구조, 규칙이 바뀌면 같은 작업 사이클 안에서 관련 문서를 함께 업데이트해야 합니다.

현지화 문서는 `notes/<locale>/...` 아래에서 관리합니다.
현지화 경로는 `README.md`와 동기화합니다.

## 커밋 전 검증

커밋을 완료하기 전에 루트 `Makefile` 훅을 통해 검증을 실행해야 합니다.

1. 필요한 경우 `make help`로 사용 가능한 워크플로 타겟을 확인합니다.
2. 변경 범위에 맞는 가장 좁은 Make 타겟을 실행합니다.
   - 백엔드 전용: `make backend-check`, `make backend-test`
   - 프론트엔드 전용: `make frontend-format-check`, `make frontend-test`
   - 공통/크로스스택 변경: `make check`, `make test`
3. 로컬 환경 문제로 필요한 Make 타겟을 실행할 수 없다면 final response와 worklog에 사유를 기록합니다.
4. Make 타겟 자체가 깨졌거나 누락된 경우가 아니라면 임의 명령으로 Make 타겟을 대체하지 않습니다.

## 워크로그 정책 (필수)

1. 모든 커밋에는 `worklog/` 아래 대응되는 워크로그 파일이 반드시 있어야 합니다.
2. 워크로그 파일명 형식: `<number>-<short-kebab-title>.md`.
3. 워크로그에는 최소 다음 항목이 포함되어야 합니다.
   - commit title
   - changed file scope
   - reason
   - impact
4. 워크로그를 업데이트/추가하지 않은 커밋은 완료 처리하면 안 됩니다.

## Git 거버넌스

브랜치, 커밋, PR을 준비할 때 저장소 하네스를 사용합니다.

```sh
make git-governance-check
```

하네스는 현재 브랜치, 커밋 제목, 대응 워크로그를 검증합니다. 커밋 또는 PR 생성 전에 메타데이터를 미리 검증하려면 `scripts/validate-git-governance.sh --commit-title "..." --pr-title "..." --pr-body-file <file>` 형식을 사용합니다.

### 브랜치 이름

브랜치 이름은 업계 표준 변경 타입과 kebab-case 설명을 사용합니다.

```text
<type>/<short-kebab-title>
```

허용 타입: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`, `style`, `revert`, `hotfix`.

예시:

- `feat/api-key-pagination`
- `fix/oauth-callback-state`
- `docs/frontend-rules`
- `chore/commit-pr-governance`

### 커밋 제목

커밋 제목은 Conventional Commits 형식을 따릅니다.

```text
<type>(optional-scope): <imperative summary>
```

예시:

- `feat(frontend): add API key pagination`
- `fix(auth): preserve oauth callback state`
- `docs: define PR governance rules`

단순하지 않은 커밋은 커밋 본문을 작성해야 하며 다음 섹션을 포함해야 합니다.

```text
Changes:
- 변경한 작업 내용.

Affected Files:
- 영향받은 주요 파일 또는 디렉터리.

Verification:
- 재현 또는 검증 방법.
```

커밋 전에 `COMMIT_BODY_FILE=<file> make git-governance-check` 또는 `scripts/validate-git-governance.sh --commit-body-file <file>`로 커밋 본문 섹션을 검증할 수 있습니다.

### Pull Request 제목과 설명

PR 제목은 눈에 보이는 타입 태그를 사용합니다.

```text
[type] Concise PR title
```

예시:

- `[feat] Add API key pagination`
- `[fix] Preserve OAuth callback state`
- `[docs] Define commit and PR governance`

PR 설명에는 다음 섹션이 필요합니다.

- Summary
- Scope
- Reason
- Verification
- Documentation
- Risk / Impact

라벨을 사용할 수 있다면 `feat`, `fix`, `docs`, `frontend`, `backend`, `infra`, `tests`처럼 변경 타입과 영향 영역에 맞는 라벨을 적용합니다.
