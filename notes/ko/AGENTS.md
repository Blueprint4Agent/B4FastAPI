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

## 루프 확인 정책

개발자가 명시적으로 루프 엔지니어링을 요청하거나 백엔드/프론트엔드 루프가 필요한지 묻는 경우, 구현 전에 관련 도메인 가이드를 확인합니다.

커밋 전에는 루프 정렬 확인을 기본 검증 단계로 취급합니다.

1. 백엔드 변경: request lifecycle, domain event, background task 루프를 따랐는지 또는 해당 없음인지 확인합니다.
2. 프론트엔드 변경: API state, realtime refresh, desktop connectivity recovery, UI composition 루프를 따랐는지 또는 해당 없음인지 확인합니다.
3. 루프를 의도적으로 건너뛰었다면 커밋되는 변경의 final response와 worklog에 이유를 기록합니다.

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

PR은 기본적으로 바로 리뷰 가능한 상태로 생성합니다. 사용자가 명시적으로 draft를 요청하거나 리뷰 전에 해결해야 할 blocker가 있을 때만 draft PR을 사용합니다.

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

## B4React 서브모듈

`src/frontend`는 B4React의 커밋을 고정한 서브모듈입니다. 가이드를 읽기 전에
`git submodule update --init --recursive`로 초기화합니다. 프론트 소스는 B4React의
이름 있는 브랜치와 PR에서 먼저 머지하고 부모의 gitlink를 갱신합니다. 부모는 패키징·통합·계약 검사를 담당합니다.
CI에서 `--remote`를 사용하거나 부모 파일로 자식 계약을 자동 덮어쓰지 않습니다.

## 프런트엔드 상태·React 성능 기본 절차

프런트엔드 런타임 작업은 고정된 B4React의 [상태·성능 정책](../../src/frontend/notes/ko/react-performance.md)을 따릅니다. 상태 소유권 검토, 동일 props로 반복되는 비용 있는 자식의 React.memo 적용 또는 미적용 이유, 실제 검증 근거를 기본으로 기록합니다. 구체적 필요 없이 Zustand/Redux를 추가하거나 모든 컴포넌트를 memo로 감싸지 않습니다. 독립적인 최적화는 별도 브랜치·작업 기록·PR로 진행합니다. 프런트엔드 작업 기록과 강제 규칙은 B4React가 소유하며 부모 기록은 통합 검사와 루프 영향을 담습니다.

`make frontend-react-performance-check`는 자식 정적·정책 검사를 호출하며 `make check`에도 간접 포함됩니다. `make frontend-test`는 렌더링·설정 회귀를, `make frontend-test-routes`는 실제 프로덕션 청크 로딩·복구를 검증합니다. 레이아웃 변경 시 브라우저 UI 검사도 실행합니다. 부모의 필수 Frontend checks CI에서도 프로덕션 라우트 검사를 실행해 gitlink 통합 시 자식 규칙을 유지합니다.

## 변경 범위별 검증

[검증 하네스](verification.md)가 작은 변경의 일괄 검사 규칙보다 우선합니다. `make verify-plan` / `make verify`로 범위를 선택하고 문서·문구에는 경량 검사만 실행합니다. 동작·UI·보호 경로는 계획에 따른 검사를 유지하며 동일 내용에 통과한 위임 검사는 반복하지 않습니다. Git 규칙·PR·필수 상태·병합 보호는 유지합니다.
