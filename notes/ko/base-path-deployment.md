# basePath를 사용하는 모놀리식 배포

[English](../base-path-deployment.md)

FastAPI가 React 빌드까지 제공하는 앱 전체를 하나의 URL 접두사 아래에 배포합니다.
기본값인 빈 문자열 또는 `/`는 기존 루트 배포를 유지합니다. 공용 Nginx, DNS,
HTTPS 인증서는 개별 앱 밖에서 운영자가 관리합니다. 서비스 이름은 하드코딩하지 않습니다.

## Docker 설정

포크한 프로젝트의 `docker/.env`에 다음과 같이 설정합니다. 이름과 포트는 예시입니다.

```dotenv
APP_BASE_PATH=/my-app
APP_BASE_URL=https://example.com/my-app
CORS_ORIGINS=https://example.com
VITE_PUBLIC_SITE_URL=https://example.com
APP_HOST_PORT=8001
COMPOSE_PROJECT_NAME=my-app
COMPOSE_FILE=docker-compose.yml
```

`APP_BASE_PATH`가 basePath 설정입니다. 영문·숫자·밑줄·하이픈과 단일 `/` 구분자를
허용하며 `/demos/my-app` 같은 중첩 경로도 가능합니다. 마지막 `/`는 정규화합니다.
URL, 쿼리, 프래그먼트, 퍼센트 인코딩, `.`·`..` 경로는 거부합니다.
`CORS_ORIGINS`와 `VITE_PUBLIC_SITE_URL`은 **접두사 없는 origin**을 유지합니다.
백엔드가 생성된 공유/소개 문서 URL을 런타임 `APP_BASE_URL`에 맞춥니다.

런타임 경로를 지원하는 이미지를 한 번 빌드한 뒤 재사용합니다.

```sh
make docker-build
DEPLOY_SOURCE=local make docker-deploy
```

`APP_BASE_PATH`는 **실행 시 설정**입니다. FastAPI가 JavaScript 실행 전에 HTML에
기준 URL과 경로 메타데이터를 넣으며 JS/CSS 빌드 파일은 동일하게 유지됩니다.
별도 프런트엔드 서버는 필요하지 않습니다. `/my-app`을 `/another-app`으로 바꾸려면
`APP_BASE_PATH`, `APP_BASE_URL`, Nginx 조각을 바꾸고
`DEPLOY_SOURCE=local make docker-deploy`로 기존 이미지를 사용해 컨테이너를 재생성합니다.
단순 `docker restart`는 수정한 Compose 환경 파일을 읽지 않습니다. 실행 중 즉시
변경되는 설정이 아니라 시작 시 읽는 설정입니다. 기본 `make docker-deploy`는 빌드를
수행하므로 기존 이미지 재사용 시 `DEPLOY_SOURCE=local`을 명시합니다.

같은 이미지를 별도 Compose 프로젝트에서 `/community`, `/tracker`, `/origin`으로
동시에 실행할 수 있습니다. 각 실행의 환경 설정과 포트만 구분합니다. 포크별 코드가
달라지면 각 코드의 빌드는 필요하지만 경로 변경만으로는 재빌드하지 않습니다.
이전 고정 경로 이미지는 이번 런타임 지원 버전으로 한 번 교체해야 하며, 이후 경로
변경에는 새 이미지가 필요하지 않습니다. 기존 고정 경로 산출물은 계속 빌드 경로
일치를 검사하며 매니페스트 없는 기존 루트 빌드도 호환됩니다.

이 구성에서는 루트 전용 Caddy HTTPS 오버레이를 사용하지 않습니다. 앱마다 Compose
프로젝트, 시크릿, 영속 데이터를 구분합니다. 코드가 같으면 이미지는 공유할 수 있습니다.
앱 포트는 기본적으로
호스트 loopback에만 바인딩합니다. Nginx도 컨테이너라면 사설 Docker 네트워크와 앱별
고유 네트워크 별칭의 8000번 포트로 연결합니다. 그 안의 `127.0.0.1`은 호스트가 아닌
Nginx 컨테이너 자체입니다. 앱 upstream 포트를 외부에 공개하지 않습니다.

## 외부 Nginx 연결

`docker/nginx/app-location.conf.template`은 기존 HTTPS `server` 블록 안에 넣는
접두사별 조각입니다. 전체 서버나 TLS 설정을 생성하는 파일은 아닙니다.

```sh
export APP_BASE_PATH=/my-app
export APP_UPSTREAM=127.0.0.1:8001
envsubst '${APP_BASE_PATH} ${APP_UPSTREAM}' \
  < docker/nginx/app-location.conf.template > /tmp/my-app.locations.conf
```

템플릿에는 마지막 `/` 없는 비어 있지 않은 경로를 사용합니다. envsubst 변수 목록을
명시해야 `$http_host` 같은 Nginx 변수가 보존됩니다. 렌더링한 파일을 기존 HTTPS
`server` 블록에서 include하고 `nginx -t` 통과 후 Nginx를 reload합니다.
DNS는 해당 서버 IP를 가리킵니다. 루트 배포는 기존 루트 프록시 구성을 사용합니다.

`proxy_pass` 뒤의 `/`를 유지해야 `/my-app/api/v1/...` 요청이 내부에서는
`/api/v1/...`로 전달됩니다. FastAPI는 URL·리다이렉트를 만들 때 외부 접두사를 복원합니다.
접두사를 그대로 전달하거나 Uvicorn `--root-path`를 추가로 설정하지 마세요.
`X-Forwarded-Prefix` 헤더를 신뢰해 경로를 결정하지 않습니다.
OAuth 콜백이 HTTPS를 유지하도록 Uvicorn의 forwarded-header 신뢰 주소를 실제 프록시
주소/사설 네트워크로 설정합니다. `docker/.env`의 `FORWARDED_ALLOW_IPS`에 실제 프록시
IP 또는 CIDR을 지정합니다. 기본값은 `127.0.0.1`이며 외부 접근 가능한 upstream에
`*`를 지정하지 않습니다. 신뢰 범위는 외부에 노출되지 않은 프록시로 제한합니다.
템플릿은 SSE 버퍼링을 끄고 docs/metrics를 비공개로 유지합니다.
DNS·인증서·공용 Nginx 설치는 자동 수행하지 않습니다.

## 로컬 또는 수동 모놀리식 패키징

```sh
make frontend-package
```

백엔드 환경에도 `APP_BASE_PATH=/my-app`과 해당 경로를 포함한 `APP_BASE_URL`을 설정하고
백엔드를 실행합니다. 접두사를 제거하는 프록시를 통해 접속합니다.
Vite를 별도 실행한다면 `src/frontend/.env`의 `VITE_BASE_PATH`를 설정하고,
`VITE_API_BASE_URL`에는 접두사를 포함한 **프록시 뒤 백엔드 공개 URL**을 지정합니다.
API만 실행하는 개발 환경에는 프런트엔드 매니페스트가 필요하지 않습니다.
데스크톱 앱의 정적 파일은 보통 `/`를 유지하고 `VITE_API_BASE_URL`만 원격 백엔드의
접두사를 포함한 URL로 설정합니다.

## 인증과 검증

브라우저 저장소 키와 refresh 쿠키 이름은 정규화된 경로로 구분합니다.
쿠키 생성·삭제 경로는 `<basePath>/`이며, 루트 배포의 기존 이름과 키는 유지합니다.
경로 변경 후에는 다시 로그인해야 하며 기존 루트 세션을 자동으로 가져오지 않습니다.
같은 origin의 경로 구분은 보안 격리나 통합 로그인을 제공하지 않습니다.
독립 앱은 시크릿과 데이터 저장소도 분리합니다.

이메일 링크는 `APP_BASE_URL`을 사용합니다. OAuth 콜백에는 접두사를 포함합니다.
예: `https://example.com/my-app/api/v1/auth/oauth/google/callback`.
결제를 활성화하면 Stripe return/webhook URL도 해당 경로로 설정합니다.
외부 제공자 설정은 자동화되지 않습니다. 타입 API 계약의 endpoint 경로는 앱 내부
기준을 유지하며, 계약에 기록된 쿠키 이름은 기본 루트 배포를 설명합니다.

공개 접두사의 끝 `/` 리다이렉트, `/my-app/home` 직접 접근·새로고침, lazy route,
이미지, `/my-app/config`, 로그인·갱신·로그아웃, SSE를 확인합니다. 다른 앱의 로그인도
유지되어야 합니다. 없는 API·정적 파일은 SPA가 아닌 404를 반환해야 합니다.
내부 헬스체크는 계속 `/health/ready`를 사용합니다. `make docker-smoke`는 내부
upstream과 패키징된 파일을 검사하며 외부 Nginx/TLS 검증을 대신하지 않습니다.

공개 소개 문서·canonical·사이트맵 URL에도 접두사가 반영됩니다. `/robots.txt`는
도메인 전체 기준이므로 공용 게이트웨이에서 정책과 사이트맵 목록을 합쳐 제공해야 합니다.
접두사 아래의 robots.txt는 생성 산출물일 뿐 도메인 전체 크롤링 정책이 아닙니다.
IndexNow도 도메인 소유권 구성을 게이트웨이에서 정리하기 전에는
`INDEXNOW_ENABLED=false`로 유지합니다.

`make base-path-deployment-test`는 임시 이미지 하나를 두 런타임 경로에 재사용해 실제 Nginx 경로,
브라우저 이동, SSE와 앱 간 세션 분리를 검증합니다. Docker·프런트엔드 의존성·
Playwright Chromium이 필요하며 테스트 컨테이너·네트워크·이미지는 정리합니다.
기존 앱 스택과 볼륨은 변경하지 않습니다.
