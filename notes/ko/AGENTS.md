# 에이전트 가이드

[English](../../AGENTS.md)

이 파일을 먼저 읽고, 작업 도메인에 맞는 가이드로 이동하세요.

## 필수 읽기 순서

1. `AGENTS.md`
2. 백엔드 작업: `src/backend/BACKEND.md`
3. 프론트엔드 작업: `src/frontend/FRONTEND.md`

## 프로젝트 초기화 트리거

개발자가 `프로젝트 초기화하기`, `새 프로젝트 시작`, `initialize this project`처럼
이 프로젝트의 초기화를 요청하면 [프로젝트 온보딩 플로우](PROJECT_ONBOARDING.md)를 읽고
단계별 정보 수집을 시작합니다. 이 저장소 지침 자체가 트리거이며 별도 스킬 설치,
슬래시 명령, GitHub 이벤트나 앱 시작 훅이 필요하지 않습니다. 이미 제공한 답은 재사용하고
다음 미응답 단계만 질문하며, 정보 수집이 끝나면 설정을 적용합니다.
초기화 방식 설명이나 이 플로우의 수정 요청은 프로젝트 초기화를 시작하지 않습니다.
재개한 세션에서는 `PROJECT_BRIEF.md`가 있으면 질문 전에 읽습니다.
실제 초기화와 리허설을 구분하고 트리거 확인은 독립 임시 복제본에서 진행합니다.
적용 전과 완료 판단 전에 필수 [표면·복구 감사](PROJECT_ONBOARDING_AUDIT.md)를 따라
UI·콘솔·문서의 잔여 브랜드, 언어 동작과 해당 표면별 검증 근거를 확인합니다.

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

1. `make verify-plan` 다음 `make verify`를 실행합니다. 실제 변경을 기준으로 최소 안전 범위를 선택합니다.
   브랜치 전체 변경은 `VERIFY_BASE=<base-sha>`로 지정하며 기본 HEAD 비교에는 스테이징·미스테이징·미추적 파일이 포함됩니다.
2. 일반 문서와 구조가 같은 번역 문구는 의존성 없는 텍스트/JSON 검사, 런타임·UI·보호/불명확한 파일은
   점진적으로 넓은 검사를 선택합니다. 불확실한 변경을 수동 강등하지 않으며 `VERIFY_FULL=1 make verify`로 확대합니다.
3. 동일 내용에 통과한 자식/위임 Make 검사는 반복하지 않습니다. 후속 수정으로 근거가 달라지면 재검사하며
   부모 통합 대상은 자체 패키징·계약을 확인합니다.
4. 선택 범위·생략한 검사와 이유를 워크로그와 최종 요약에 기록합니다. Git 규칙·리뷰 가능한 PR·병합 보호는 유지합니다.
5. [변경 범위별 검증](verification.md)을 따릅니다. 관련 후속 수정은 하나의 작업 PR에서 마무리하고
   자식 병합 후 부모 gitlink를 갱신합니다. 로그 요약부터 확인하며 CI 감시는 하나만 사용합니다.

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

### 병합 방식

기본 병합은 자동 병합을 포함해 merge commit입니다.

```sh
gh pr merge <번호> --auto --merge
```

Squash/rebase는 사용자가 명시적으로 요청한 경우만 허용합니다.
`make git-governance-check`의 기본 `MERGE_METHOD=merge`가 다른 방식을 거부하며,
명시적 요청이 있을 때만 `ALLOW_NON_MERGE_METHOD=true`를 사용합니다.
자동 병합을 등록하면 실제 `autoMergeRequest` 방식을 확인합니다. 잘못 등록했다면
필수 검사가 끝나기 전에 자동 병합을 해제하고 `--merge`로 다시 등록합니다.
이미 병합된 PR의 방식은 변경할 수 없습니다.

## B4React 서브모듈

`src/frontend`는 B4React의 커밋을 고정한 서브모듈입니다. 가이드를 읽기 전에
`git submodule update --init --recursive`로 초기화합니다. 프론트 소스는 B4React의
이름 있는 브랜치와 PR에서 먼저 머지하고 부모의 gitlink를 갱신합니다. 부모는 패키징·통합·계약 검사를 담당합니다.
CI에서 `--remote`를 사용하거나 부모 파일로 자식 계약을 자동 덮어쓰지 않습니다.

## 프런트엔드 상태·React 성능 기본 절차

프런트엔드 런타임 작업은 고정된 B4React의 [상태·성능 정책](../../src/frontend/notes/ko/react-performance.md)을 따릅니다. 상태 소유권 검토, 동일 props로 반복되는 비용 있는 자식의 React.memo 적용 또는 미적용 이유, 실제 검증 근거를 기본으로 기록합니다. 구체적 필요 없이 Zustand/Redux를 추가하거나 모든 컴포넌트를 memo로 감싸지 않습니다. 독립적인 최적화는 별도 브랜치·작업 기록·PR로 진행합니다. 프런트엔드 작업 기록과 강제 규칙은 B4React가 소유하며 부모 기록은 통합 검사와 루프 영향을 담습니다.

`make frontend-react-performance-check`는 자식 정적·정책 검사를 호출하며 `make check`에도 간접 포함됩니다. `make frontend-test`는 렌더링·설정 회귀를, `make frontend-test-routes`는 실제 프로덕션 청크 로딩·복구를 검증합니다. 레이아웃 변경 시 브라우저 UI 검사도 실행합니다. 부모 로컬 전체 검증에서도 프로덕션 라우트 검사를 실행해 gitlink 통합 시 자식 규칙을 유지합니다.

## 변경 범위별 검증

[검증 하네스](verification.md)가 작은 변경의 일괄 검사 규칙보다 우선합니다. `make verify-plan` / `make verify`로 범위를 선택하고 문서·문구에는 경량 검사만 실행합니다. 동작·UI·보호 경로는 계획에 따른 검사를 유지하며 동일 내용에 통과한 위임 검사는 반복하지 않습니다. 로컬 Git 규칙·PR·병합 보호는 유지하고 GitHub 필수 검사 상태는 제거합니다.

## 작업 시작과 완료 순서

1. 관련 가이드와 작업 트리/서브모듈 상태를 확인하고 무관한 변경을 보존합니다.
2. 구현 전에 대상 브랜치에서 이름 있는 작업 브랜치를 만듭니다.
3. `.github/WORKLOG_TEMPLATE.md`를 다음 번호의 `worklog/NNNN-description.md`로 복사합니다.
   구현 전에 커밋 제목·이유·범위·설계·검증 계획·루프 영향을 작성합니다.
4. 구현과 관련 문서를 동기화하고 범위가 바뀌면 계획도 갱신합니다.
5. 루트 Make 검사를 실행하고 이번 작업에서 생략한 검사와 이유를 기록합니다.
   과거의 검사 생략 요청은 영구 면제가 아닙니다.
6. 완료된 워크로그를 포함해 의도한 파일만 스테이징한 뒤
   `COMMIT_TITLE='type(scope): summary' COMMIT_BODY_FILE=/tmp/commit.txt make git-governance-check`를 실행합니다.
   계획 검증은 Git index를 읽으므로 스테이징 변경 후 다시 확인합니다.
7. 커밋·푸시 후 리뷰 가능한 PR을 만들고 PR_TITLE과 PR_BODY_FILE을 함께 검사합니다.
8. 로컬 훅과 실제 PR 메타데이터를 병합 전에 확인하며 기본 merge commit을 사용합니다.
   자동 병합이 등록됐다면 MERGE 방식인지 확인합니다.

템플릿에는 Design, Verification Plan, Loop Alignment, Verification도 필요합니다.
각 작성 커밋의 워크로그 Commit Title은 커밋과 정확히 일치해야 하며 통합 merge commit은 제외합니다.
Git은 계획 작성 시점을 증명하지 못하므로 시작 시 계획은 작업자의 의무입니다.
로컬 규칙은 기록·메타데이터를 검사하며 설계의 정확성을 증명하지 않습니다.

## 로컬 규칙과 수동 GitHub 워크플로

clone마다 `make hooks-install`을 한 번 실행합니다(`make init`에도 포함).
초기화된 프론트 서브모듈에도 설치하며 기존 사용자 지정 `core.hooksPath`는 보존합니다.

`commit-msg`는 실제 메시지와 스테이징된 워크로그를 확인하고 통합 merge commit은 제외합니다.
`pre-push`는 서브모듈까지 깨끗한 작업 트리와 현재 HEAD의 정확한 푸시를 요구합니다.
원격 main을 가져와 merge-base 이후 모든 작성 커밋과 전체 브랜치 범위의
`make verify-plan`·`make verify`를 검사합니다. 실패하면 푸시를 막으며 일반 작업에서 우회하지 않습니다.

PR 메타데이터 생성/수정 후와 병합 직전에 `PR_NUMBER=<번호> make git-governance-pr-check`로
실제 GitHub 제목/본문과 전체 커밋 범위를 로컬에서 검사합니다. PR_TITLE/PR_BODY_FILE
사전 검증도 유지합니다. GitHub에서 수정한 메타데이터는 로컬 훅을 실행하지 않습니다.

이미지·데스크톱을 포함한 모든 GitHub 워크플로는 workflow_dispatch 수동 실행만 유지합니다.
PR/push/예약/태그/릴리스 자동 실행은 없으며 main의 PR·대화 해결·삭제/비 fast-forward 보호와
필수 승인 0개를 유지합니다. `.github/main-ruleset.json`과 실제 ruleset의 필수 상태 검사는
제거돼 있습니다. 로컬 훅은 우회 가능하므로 서버 CI 보장이 아닙니다. PR·이력 보호를 끄지 않으며
ruleset 변경에는 관리자 권한이 필요하고 없는 권한을 우회하지 않습니다.

성공 기록은 내용에 결합된 로컬 receipt로 최대 24시간 재사용합니다. 코드·문서·설정·도구/환경·
필수 빌드 산출물이 같아야 합니다. worklog 결과만 수정해도 텍스트/거버넌스는 검사하며
CI/수동 Actions와 `VERIFY_FULL=1`은 receipt를 사용하지 않습니다. [로컬 훅](local-hooks.md)을 참고하세요.

## 페이지 유형별 일관성

UI 작업은 고정된 [페이지 일관성 정책](../../src/frontend/notes/ko/page-families.md)을 따릅니다.
구현 전에 비교할 기존 화면을 정하고 셸·간격·표면·타이포그래피·동작·반응형 규칙을 재사용합니다.
참고 이미지는 기존 페이지 유형의 규칙을 덮어쓰지 않습니다. 커밋 전에 자식 Page Family
워크로그와 실제 비교를 남기며 공용 컨트롤 검사만으로 페이지 일관성을 판단하지 않습니다.
예외는 적용 범위와 이유를 기록합니다.
