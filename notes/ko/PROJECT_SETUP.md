# 새 프로젝트 초기화

블루프린트를 복사하고 `make frontend-init`으로 프론트엔드 서브모듈을 준비한 뒤 사용합니다. 의존성은 `make install`로 설치합니다. 기존 `make init`은 env 파일만 초기화하는 동작을 유지합니다.

```sh
cp project.example.json project.json
# project.json의 공개 설정값 수정
make project-plan
make project-init
make project-check
```

`project-plan`은 입력을 검증하고 변경할 파일 경로만 보여줍니다. 파일을 쓰거나 env 값을 출력하지 않습니다. `project-init`은 변경 전 파일을 Git에서 제외된 `.project-backups/<timestamp>/`에 백업하고 적용합니다. 같은 설정으로 다시 실행하면 변경하지 않습니다. `project-check`는 생성된 설정이 달라지면 실패하므로 초기화를 다시 실행해 맞춥니다. 다른 경로는 `PROJECT_CONFIG=path/to/project.json make project-init`으로 지정합니다. 로고 경로는 해당 manifest 기준입니다. 기본 CI/Docker 흐름에는 루트 `project.json`을 사용하세요.

| 필드 | 적용 범위 |
| --- | --- |
| `version` | 설정 형식 버전, 현재 `1` |
| `slug` | 소문자 kebab-case 서비스 키, Docker 이미지/Compose 프로젝트명, 관측용 서비스명 |
| `name` | 브라우저 제목, 공개 내비게이션, 이메일 브랜드, API 앱 이름, 데스크톱 제품/창 제목 |
| `short_name` | 내비게이션/사이드바 공통 브랜드 문구 |
| `identifier` | Tauri 앱 식별자, 예: `com.example.myapp` |
| `features.login` | 기존 백엔드 `LOGIN_ENABLED` 설정 |
| `features.email` | 기존 백엔드 `EMAIL_ENABLED` 설정 |
| `features.oauth` | 기존 백엔드 `OAUTH_ENABLED` 설정 |
| `logo`, `logo_dark` | `branding/` 아래의 선택적 공개 이미지 경로 |

이름에는 문자, 숫자, 공백과 `_ . & ( ) -`를 사용할 수 있으며 길이는 각각 60자/16자까지입니다. 이메일/OAuth를 켜려면 로그인이 활성화되어야 합니다. SMTP, OAuth 제공자 인증 정보와 콜백 URL은 별도로 설정해야 합니다. 런타임 기능 노출은 기존 백엔드 `/config`가 결정하며 설정 UI는 추가하지 않습니다.

로고를 사용하는 예시입니다.

```json
{
  "version": 1,
  "slug": "acme",
  "name": "Acme",
  "short_name": "ACME",
  "identifier": "com.acme.desktop",
  "features": { "login": true, "email": false, "oauth": false },
  "logo": "branding/logo.svg",
  "logo_dark": "branding/logo-dark.svg"
}
```

직접 관리하는 SVG/PNG/WEBP/JPEG 공개 이미지를 파일당 2 MB까지 지원합니다. 다크 로고가 없으면 양쪽 테마에 기본 로고를 사용합니다. 로고가 없으면 템플릿 이미지를 유지합니다. 로고 필드를 제거하면 기본 참조로 돌아가며 이전 생성 이미지 파일은 자동 삭제하지 않습니다. Tauri 설치 파일/네이티브 아이콘(`src-tauri/icons`)은 별도입니다. npm/Python/Rust 소스 패키지·모듈 이름은 변경하지 않습니다.

초기화 명령은 백엔드/Docker env에서 브랜드와 세 가지 기능 키를 관리합니다. DB 연결과 설정된 비밀키 등 나머지 값은 보존하고 빠진 템플릿 기본값을 채웁니다. 비밀키가 없거나 비어 있거나 `CHANGE_ME`이면 생성합니다. 프론트엔드 env도 기존 값을 보존하며 자체 예시와 동기화합니다. DB 접속이나 마이그레이션은 하지 않습니다. Compose 프로젝트명을 바꾸면 리소스 이름 공간이 달라지므로 새 복제 프로젝트용으로 사용하며 운영 배포 이전 용도로 사용하지 않습니다.

복제한 부모 저장소에 공개 `project.json`과 원본 로고를 커밋하세요. 인증 정보는 무시된 env 또는 배포 비밀 저장소에 둡니다. 부모는 서브모듈 내부에 Git에서 제외된 `project.local.json`과 `public/project-brand/`를 생성합니다. 이를 서브모듈 커밋에 포함하지 않습니다. `make project-brand`, `make frontend-build`, `make frontend-test-routes`와 Docker 브랜드 단계는 비밀값을 읽지 않고 공개 빌드 입력을 다시 생성합니다. Docker는 루트 `project.json`을 사용합니다. 루트 manifest가 없으면 기존/기본 프론트엔드 설정을 유지합니다. 기능을 바꾼 뒤에는 `make project-init`과 백엔드 재시작이 필요하며, 브랜드를 바꾼 뒤에는 프론트엔드 개발 서버 재시작 또는 재빌드가 필요합니다.

B4React 단독 사용은 자체 README를 참고하세요. 자식 빌드 도구는 부모 파일을 읽지 않습니다. 데스크톱 브랜드 적용은 npm/Make Tauri 실행기를 사용합니다. 원시 Tauri 바이너리를 직접 실행하면 이 설정 병합을 거치지 않습니다.

검증: `make project-init-check project-init-test`는 초기화와 기존 값 보존을 확인합니다. `make project-build-test`는 임시 디렉터리에서 사용자 지정 한글/영문 브랜드와 로고를 빌드하고 실제 브라우저 렌더링을 확인합니다. 프론트엔드 의존성과 Playwright Chromium이 필요합니다. 네이티브 패키징은 별도의 플랫폼 도구가 필요하며 이 브라우저 검증에 포함되지 않습니다.
