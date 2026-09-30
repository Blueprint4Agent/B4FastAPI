# 로컬 Git 검증

clone 후 `make hooks-install` 또는 `make init`을 실행합니다. 이 clone에만
`core.hooksPath=.githooks`를 설정합니다. Git은 clone할 때 훅을 자동 활성화하지 않습니다.
B4FastAPI는 초기화된 B4React 서브모듈에도 설치합니다. 다른 hooksPath는 덮어쓰지 않습니다.

- 커밋 훅: 실제 커밋 제목·본문과 스테이징된 일치 워크로그를 검사합니다. 통합 merge commit은 제외합니다.
- 푸시 훅: 서브모듈·미추적 파일까지 작업 트리가 깨끗하고 푸시 대상이 현재 HEAD인지 확인합니다.
  해당 원격 main을 가져와 merge-base부터 브랜치 전체 커밋을 검증하고 기존 `make verify-plan`,
  `make verify`를 실행합니다. 이력·네트워크·의존성이 없거나 검사에 실패하면 푸시를 막습니다.
- PR 생성·제목/본문 수정 후와 병합 직전에 `PR_NUMBER=123 make git-governance-pr-check`를 실행합니다.
  현재 HEAD와 실제 GitHub PR 메타데이터를 검사합니다. PR_TITLE/PR_BODY_FILE 사전 검증도 유지합니다.

문서·번역은 경량 검사, 동작·UI·보호 영역은 기존 범위별 검사를 그대로 적용합니다.
`make hooks-test`는 격리 Git 저장소에서 커밋/푸시 차단·성공과 캐시 무효화를 검증하며 전체 검사에 포함됩니다.

검사 로그는 Git 디렉터리의 `verification-logs/`, 성공 기록은 `verification-receipts/`에 저장합니다.
성공 기록은 최대 24시간 동안 명령·소스/문서 내용과 권한·로컬 설정·도구/환경·필요한 빌드 산출물이
동일할 때만 재사용합니다. 결과 기록용 worklog Markdown은 무거운 검사 지문에서 제외하지만
텍스트와 커밋 규칙은 매번 검사합니다. 파일 추가/삭제/수정, 설정·도구 변경, 실패한 재검사,
만료/손상 기록, 사라진 산출물은 재사용을 막습니다. 부모 위임 검사는 동일한 자식 검사 결과를
재사용할 수 있으며 계약·브랜딩·패키징 통합은 필요한 대로 실행합니다. 서버 검증 증명은 아닙니다.
`VERIFY_FULL=1 make verify`는 전체 재검사를 강제하며 수동 GitHub 실행은 로컬 기록을 쓰지 않습니다.

GitHub Actions는 Run workflow 또는 `gh workflow run`으로만 실행합니다. 거버넌스에는 PR 번호를
지정합니다. Build는 ref/PR 검증과 명시적 이미지 발행, Desktop Build는 선택 ref의 수동 빌드를
유지합니다. PR/push/예약/태그/릴리스 자동 실행은 없습니다. main의 PR·대화 해결·삭제/강제 푸시
금지는 유지하고 필수 CI 상태만 제거합니다. 필수 승인 수는 0입니다.

훅은 미설치하거나 우회할 수 있어 GitHub가 검사 통과를 보장하지 않습니다. 기여자/에이전트는 훅 설치,
워크로그, 실제 PR 검증과 PR 병합 절차를 지키며 일반 작업에서 훅을 건너뛰지 않습니다.
