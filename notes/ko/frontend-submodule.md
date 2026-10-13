# B4React 통합

B4FastAPI는 백엔드·OpenAPI 내보내기·통합 패키징·릴리스 CI를 소유합니다.
B4React는 프론트 소스·테스트·데스크톱 셸·고정 계약·생성 타입을 소유합니다.
`src/frontend`는 파일 사본 대신 특정 Git 커밋을 기록합니다.

## 체크아웃과 변경

```sh
git clone --recurse-submodules https://github.com/Blueprint4Agent/B4FastAPI.git
# 기존 복제본 또는 부모 브랜치 전환 후
git submodule update --init --recursive
make install init
```

서브모듈은 보통 detached HEAD입니다. 프론트 수정은 내부에서 이름 있는 브랜치를 만들고
B4React PR로 머지합니다. 커밋 전환 전에 로컬 수정사항을 보존하세요.
머지 후 부모에서 실행합니다.

```sh
git -C src/frontend fetch origin
# 실제 검토된 커밋 SHA로 치환
git -C src/frontend checkout <reviewed-commit-sha>
make check test build
git add src/frontend
```

부모 worklog와 함께 포인터를 커밋하고 PR을 만듭니다. 롤백은 부모 포인터 변경을 되돌린 후
서브모듈을 다시 초기화합니다. CI는 `--remote`를 사용하지 않습니다.

## 계약 변경 순서

1. 제공자 브랜치에서 FastAPI 선언을 수정하고 `make contract-export`를 실행합니다.
2. B4React 브랜치에 검토한 스냅샷을 도입하고 `contracts/source.json`에 제공자 소스 커밋을 기록합니다.
   타입 생성·호출부 변경 후 자식 Make 검사·테스트·빌드를 실행합니다.
3. B4React를 먼저 머지한 뒤 부모 PR에 해당 커밋을 고정하고 `make check test build`를 실행합니다.

부모의 JSON 의미상 동등성 검사는 메타데이터를 포함한 정확한 기준 일치를 요구합니다.
추가 필드 변경도 명시적인 프론트 계약 도입이 필요합니다. 백엔드별로 다른 프론트 버전을 선택할 수 있습니다.
스키마 비교는 인증·에러·쿠키·리다이렉트·readiness·SSE 동작 테스트를 대체하지 않습니다.
Spring Boot도 같은 계약과 자체 dist 패키징 어댑터를 구현해야 합니다.

## 빌드 책임

`make frontend-build`는 자식 dist만 생성합니다. `make frontend-package`는 빌드 결과를
`src/backend/app/static/dist`에 복사하고 `make build`도 이 패키징을 포함합니다.
Docker는 다단계 빌드에서 직접 복사합니다. 별도 웹 호스팅도 가능하며 API URL·CORS·쿠키 설정이 필요합니다.

## 서비스 레이아웃

고정된 프론트엔드는 `sidebar`(기본), `topnav`, `focused`(미니멀형)를 지원합니다.
서비스 기본값은 B4React 변경에서 `src/frontend/src/service.config.ts`를 수정한 뒤 다시 빌드합니다.
서버 `APP_MODE=development`일 때만 설정 → 모양 → 레이아웃에서 브라우저 미리보기를 제공하며
운영 모드는 저장된 미리보기를 무시합니다. 사이드바 없는 설정·관리자 화면의 하위 메뉴는
상단 전체 메뉴 대신 본문 옆 박스로 표시합니다. [한국어](../../src/frontend/notes/ko/layout-modes.md)와
[English](../../src/frontend/notes/layout-modes.md)를 참고하세요. 백엔드 API나 Docker 빌드 인자는
추가하지 않으며 GHCR 빌드는 고정된 프론트엔드 소스 기본값을 사용합니다.

## 홈 랜딩

홈은 반응형 소개와 실제 데모 화면 미리보기, 기능 카드·개발 흐름·활용 예시와 상단 고정 섹션 링크,
제품·자료·계정 푸터로 구성됩니다. 선택한 서비스 레이아웃과 로그인·역할별 경로는 유지합니다.
MainPageTemplate은 설정 형태의 메뉴 화면을 위해 계속 제공됩니다.
자식의 [페이지 계열 규칙](../../src/frontend/notes/ko/page-families.md#홈-랜딩)과
[홈·템플릿 가이드](../../src/frontend/notes/ko/main-page-template.md)를 참고하세요.
새 API·외부 이미지 호스트·배포 변수는 필요하지 않으며 /about/은 정적 페이지로 유지합니다.

상단 메뉴·미니멀형은 헤더 중앙의 텍스트 링크를, 사이드바형은 캡슐을 사용합니다. 미리보기는 마우스·초점이 머물러도 진행선과 함께 6초마다 부드럽게 전환됩니다. 명시적 정지, 확대, 화면 밖·숨긴 탭, 동작 줄이기에서는 멈춥니다. 푸터 배경은 본문 전체 폭을 채웁니다.
