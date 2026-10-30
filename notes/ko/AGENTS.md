# 에이전트 가이드

[English](../../AGENTS.md)

## 읽기 순서와 작업별 진입점

이 문서를 먼저 읽고 백엔드는 `src/backend/BACKEND.md`, 프런트엔드는 초기화된
B4React의 `AGENTS.md`와 `FRONTEND.md`를 읽습니다. 테스트 변경은 도메인 TEST 가이드도
읽습니다. 무관한 작업 트리와 서브모듈 변경은 보존합니다.

실행 절차는 저장소 스킬에 둡니다. 스킬 자동 탐색이 없는 클라이언트도 해당 파일을 읽습니다.

| 작업 | 절차 |
| --- | --- |
| 커밋 준비·생성 | [b4-commit](../../.agents/skills/b4-commit/SKILL.md) |
| PR 게시·수정 또는 요청된 병합 | [b4-pr](../../.agents/skills/b4-pr/SKILL.md) |
| GitHub 이슈 생성·수정 | [b4-issue](../../.agents/skills/b4-issue/SKILL.md) |

요청 범위를 따릅니다. 커밋만 요청하면 이슈·병합까지 확대하지 않습니다. 구현 작업은
사용자가 게시를 제한하지 않는 한 커밋·푸시·ready PR까지 마칩니다. 검토만 요청한 경우
변경을 게시할 필요가 없습니다.

## 필수 작업 규칙

- 구현 전에 `<type>/<kebab-description>` 작업 브랜치를 만들고
  [워크로그 템플릿](../../.github/WORKLOG_TEMPLATE.md)을 다음 번호의
  `worklog/NNNN-description.md`로 복사해 계획·설계·루프 영향을 먼저 작성합니다.
- 각 작성 커밋은 Commit Title이 정확히 일치하는 완성된 워크로그를 추가·수정합니다.
  통합 merge commit은 제외합니다. Git은 기록을 검사하며 계획 시점이나 설계 정확성을 증명하지 않습니다.
- 루트 `make verify-plan` 다음 `make verify`를 실행합니다. 브랜치 전체는
  `VERIFY_BASE=<base-sha>`를 사용합니다. 범위·확대·receipt는 [검증 정책](verification.md)을
  따릅니다. 불확실한 변경을 강등하거나 유효한 동일 검사를 반복하지 않습니다.
  실제 결과와 이번 작업의 생략 사유를 워크로그·최종 답변에 기록합니다. 과거 생략 요청은 영구 면제가 아닙니다.
- clone마다 `make hooks-install`로 훅을 설치합니다(`make init`에도 포함).
  훅을 우회하지 않으며 기존 사용자 지정 hooksPath는 명시적으로 조정합니다.
  훅 동작과 수동 Actions는 [로컬 훅](local-hooks.md)을 참고합니다.
- 모든 작성 커밋은 Conventional Commit 제목과 내용이 있는 Changes, Affected Files,
  Verification 본문을 사용합니다. 스테이징한 메타데이터를 Make로 검사합니다.
- 기존 GitHub 템플릿을 사용합니다. PR은 기본 ready이며 명시적 요청이나 blocker가 있을 때만
  draft를 사용합니다. 관련 후속 수정은 같은 작업 PR에서 마칩니다.
- 기본 병합은 merge commit입니다. squash/rebase는 명시적 사용자 요청이 필요합니다.
  PR 생성·수정 후와 요청된 병합 직전에 실제 메타데이터를 검사합니다.
  PR·이력 보호를 끄거나 저장소 관리자 권한을 우회하지 않습니다.
- 동작·구조·규칙 변경 시 `notes/ko/`를 포함한 관련 문서를 동기화하고 README의 번역 진입점도 맞춥니다.

## 프로젝트 초기화 트리거

`프로젝트 초기화하기`, `새 프로젝트 시작`, `initialize this project` 요청은
[온보딩](PROJECT_ONBOARDING.md)의 단계별 정보 수집을 시작합니다. 저장소 지침 자체가
트리거이며 별도 스킬·슬래시 명령·GitHub 이벤트·앱 훅이 필요하지 않습니다.
기존 답은 재사용하고 다음 미응답 단계만 질문하며 수집 완료 후 적용합니다.
설명·워크플로 수정 요청은 초기화를 시작하지 않습니다. 재개 시 `PROJECT_BRIEF.md`를 먼저 읽습니다.
실제 적용과 리허설을 구분하고 트리거 검사는 독립 임시 복제본에서 진행합니다.
적용·완료 판단 전 [표면·복구 감사](PROJECT_ONBOARDING_AUDIT.md)에 따라 브랜드 잔여물,
언어 동작과 UI·콘솔·문서 등 해당 표면별 근거를 확인합니다.

## B4React 통합

`src/frontend`는 별도 저장소의 고정 커밋입니다. 로컬 변경을 보존한 뒤 필요한 서브모듈을
`git submodule update --init --recursive`로 초기화합니다. 프런트 변경은 자식 브랜치·PR에서
먼저 병합하고 부모 pin을 갱신합니다. 부모 기록은 통합·계약·패키징, 자식 기록은 프런트 변경을
담습니다. CI에서 `--remote`를 따르거나 공급자 계약으로 자식 계약을 자동 덮어쓰지 않습니다.
[통합·계약 순서](frontend-submodule.md)를 따릅니다.

## 도메인 검토 의무

시작·완료 시 백엔드 요청·도메인 이벤트·백그라운드 작업과 프런트 API 상태·실시간 갱신·
데스크톱 복구·UI 구성 루프를 검토합니다. 해당 없음·생략 이유를 기록하며 명시적 루프 요청은
구현 전에 도메인 가이드를 읽습니다.

백엔드 서비스는 조율하고 저장소가 관계형 세션·쿼리·트랜잭션·ORM 쓰기·드라이버 오류를 소유합니다.
`src/backend/BACKEND.md`의 영속성·라우터/서비스 경계를 수동 검토하며 main.py 핸들러,
도메인 오류, 다른 서비스 private 접근도 확인합니다. import 검사 통과만으로 준수를 보장하지 않습니다.
책임 위반·일관성·허용된 기술/전송 어댑터를 구분하며 Redis는 관계형 경계에서 제외합니다.

프런트 런타임은 자식 [상태·성능 정책](../../src/frontend/notes/ko/react-performance.md)에 따라
소유권·memo 적용 근거·관측 결과를 기록합니다. 근거 없는 일괄 memo·상태 라이브러리 도입을
피하며 독립 최적화는 별도 작업 PR로 둡니다. UI는 [페이지 정책](../../src/frontend/notes/ko/page-families.md)에
따라 구현 전 비교 화면을 정하고 구성을 재사용하며 실제 렌더링과 예외를 기록합니다.
참고 이미지는 기존 페이지 유형의 규칙을 덮어쓰지 않습니다.
