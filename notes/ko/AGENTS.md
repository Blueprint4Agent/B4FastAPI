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
