# 모놀로식 서버 배포

[English](../monolithic-deployment.md)

초기 운영 구조는 브라우저 → 선택적 Cloudflare DNS/프록시 → Caddy HTTPS →
FastAPI 컨테이너 하나입니다. FastAPI가 `/api/v1`, `/config`, 빌드된 React SPA를
함께 제공합니다. PostgreSQL·Redis·선택적 메일 워커를 내부에서 실행하거나 기존
외부 서비스에 연결합니다. 프론트엔드 서버는 별도로 띄우지 않습니다.
이 구성에서 Cloudflare는 앞단이며 Docker 원본 서버는 AWS EC2 같은 호스트에
있어야 합니다. 프론트·백엔드 분리와 nginx 구성은 후속 범위입니다.

## 1. 서버 준비

Linux 서버에 Docker Engine·Compose 플러그인·Python 3·Git·Make를 준비합니다.
Compose는 `up --wait --wait-timeout`, `run --pull never`를 지원해야 합니다.
Node·uv·앱 Python 의존성은 이미지 빌드 안에서 설치합니다. Docker 볼륨용 영속 디스크와
빌드에 충분한 메모리·디스크를 확보하세요. 운영 서버에서 빌드하지 않으려면 검증된
사전 빌드 이미지를 사용합니다. EC2 arm64/amd64 등 서버 CPU와 이미지 아키텍처가
일치해야 합니다.

AWS에서는 고정된 공개 주소와 TCP 80/443 보안 그룹 규칙을 준비합니다. SSH는
운영자 주소로 제한하거나 구성한 관리 채널을 사용합니다. 앱 8000·PostgreSQL 5432·
Redis 6379·관측 도구 포트를 인터넷에 열지 마세요.
[AWS 보안 그룹 안내](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html)를 참고하세요.

도메인의 A 레코드를 설정하고 IPv6를 실제 구성한 경우에만 AAAA를 추가합니다.
Cloudflare는 먼저 DNS-only로 원본 HTTPS·인증서 발급을 확인한 뒤 필요하면 프록시를
켜고 [Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/)를
사용하세요. 원본 인증서와 갱신 검증 경로를 유지합니다. HTTPS 리다이렉트 원본에
Flexible을 사용하지 마세요. `/api/*`, `/config`, `/health/*`, 인증 페이지와 SSE에는
전체 캐시 규칙을 적용하지 않습니다. Cloudflare 경유 로그인·OAuth·웹훅·스트리밍도
다시 확인하세요. 앞단 정책이 해당 동작에 영향을 줄 수 있습니다.

## 2. 새 설치 초기화

```sh
git clone --recurse-submodules https://github.com/Blueprint4Agent/B4FastAPI.git
cd B4FastAPI
make docker-init PUBLIC_DOMAIN=app.example.com
```

실제 소유한 도메인으로 바꾸세요. **새** `docker/.env`에 무작위 서명 키·DB/Redis
비밀번호를 생성하며 권한은 0600입니다. 비밀값을 출력하거나 기존 파일을 덮어쓰지
않습니다. 기존 .env 방식이며 비밀 파일·Secret Manager 기능을 추가한 것은 아닙니다.

배포 전 서버에서 `docker/.env`를 검토합니다.

- `APP_MODE=production`, `LOGIN_ENABLED=true`를 유지합니다.
- 데이터 생성 **전** 설치별 `COMPOSE_PROJECT_NAME`을 정합니다. 네트워크·볼륨을
  선택하는 값이므로 업데이트 때 바꾸면 안 됩니다.
- `APP_IMAGE`를 빌드·배포할 릴리스 태그로 정합니다. 사전 빌드 이미지는 명시적
  버전 태그나 레지스트리 digest를 권장하며 이전 이미지 참조도 기록합니다.
- 기본은 로컬 PostgreSQL·Redis입니다. 외부 서비스는 실제 연결값을 입력합니다.
  생성된 비밀번호가 외부 서비스의 계정 설정을 변경하지는 않습니다.
- 이메일·OAuth·Stripe는 제공업체 설정과 검증 전까지 비활성 상태를 유지합니다.
  외부 저장소도 별도 제공업체 설정이 필요합니다.
- HTTPS 초기화는 `PUBLIC_DOMAIN`, `APP_BASE_URL`, CORS, 공유 주소를 맞추고
  `COMPOSE_FILE=docker-compose.yml:docker-compose.https.yml`을 저장합니다.

기존 설치의 키를 새로 생성하지 마세요. 프로젝트 이름·인증정보·데이터 경로를 유지하고
필요한 값을 명시적으로 편집합니다. 선택적 개발 도구 `make docker-env-sync`는 uv를
요구하며 기존 값을 보존합니다. 데이터 백업과 DB 계정 비밀번호 변경은 별도 작업입니다.
`docker-check`는 실행 설정 사전 점검이며 주석·배치 동기화 검사가 아닙니다.

별도 파일은 `DOCKER_ENV_FILE=/absolute/path/production.env make docker-check`처럼
선택하고 다른 핵심 Docker 명령에도 동일하게 전달하세요. 상대 경로는 호출 위치를
기준으로 해석합니다. 파일은 Git 밖에 보관하고 내용을 커밋하지 않습니다. Compose
치환에서는 셸 값이 우선하므로 배포를 바꿀 때 남아 있는 `COMPOSE_FILE`, `PUBLIC_DOMAIN`,
`APP_IMAGE` 셸 변수를 확인하세요.

## 3. 점검과 배포

```sh
make docker-check
make docker-deploy
make docker-status
```

`docker-check`는 전체 설정을 출력하지 않고 실제 Compose 설정을 해석합니다.
운영 기본 키·휘발성 SQLite 경로·HTTPS 주소 불일치를 거부하고 Docker 데몬 접근을
확인합니다. 외부 제공업체 연결이나 DNS·인증서 발급 성공을 보장하지는 않습니다.

`docker-deploy`는 이미지를 준비하고 **이미지 안의 설정 클래스**로 검사한 뒤 로컬
DB/Redis → 필요 시 메일 워커 → API → 선택된 Caddy 순서로 준비 상태를 기다립니다.
기존 DB/Redis 컨테이너는 재생성하지 않습니다. 단일 인스턴스의 앱·워커·프록시 재생성
중에는 잠깐 중단될 수 있습니다. 같은 프로젝트에 배포 명령을 동시에 실행하지 마세요.
Beat·관측 도구는 계속 선택 사항입니다. 사용 중이라면 작업·관측 요건을 확인하고
같은 릴리스·환경 구성으로 명시적으로 갱신하세요.

성공 조건에는 HTTP readiness·실행 모드·SPA·JavaScript 자산과 Caddy 경유 메트릭·
문서·OpenAPI 차단이 포함됩니다. 공개 HTTPS 검사에서 인증서 검증을 끄지 않습니다.
서비스별 준비 대기와 HTTP 재시도 구간은 각각 기본 120초이며
`HEALTH_TIMEOUT_SECONDS=180 make docker-deploy`로 조절합니다. 실패하면 0이 아닌
종료 코드를 반환하고 성공으로 보고하지 않습니다. DB 마이그레이션 자동 롤백이나
이미지 tar 생성은 수행하지 않습니다.

```sh
make docker-deploy DEPLOY_SOURCE=build  # 기본: 현재 체크아웃 빌드
make docker-deploy DEPLOY_SOURCE=pull   # APP_IMAGE 가져오기, 사전 레지스트리 인증 필요
make docker-deploy DEPLOY_SOURCE=local  # 이미 빌드/로드된 이미지 사용
```

pull/local 이미지는 블루프린트 실행 파일·healthcheck·프론트엔드를 포함해야 합니다.
사전 빌드 이미지의 이름·공유 설정은 이미 내장되어 있어 서버 .env 변경만으로 갱신되지
않습니다. 오프라인 전달이 필요할 때만 `make docker-export` / `docker load -i <archive>`를
사용하세요. `make docker-build`는 기동 없이 이미지 빌드·설정 검증을 수행합니다.
`make docker-up`은 강제 재생성이나 외부 HTTP 검증 없이 준비된 이미지를 기동합니다.

## 4. 운영·업데이트·복구

```sh
make docker-status
make docker-smoke
make docker-logs DOCKER_SERVICE=app
make docker-logs DOCKER_SERVICE=caddy
```

업데이트 전 `docker-status`로 현재 이미지 식별자를 기록하고 PostgreSQL 또는 SQLite와
비공개 객체 데이터를 백업하며 복구 절차를 확인합니다.
[DB 백업 안내](backend/DB_BACKUP_RESTORE.md)를 참고하세요. 이미지 tar는 DB·객체 데이터
백업이 아닙니다. 업데이트 과정에서 `down -v`, 볼륨 prune, 프로젝트 이름 변경을 하지 마세요.

검토된 부모 리비전으로 갱신하고 `git submodule update --init --recursive`로 고정된
프론트엔드를 사용합니다. 릴리스 변경·마이그레이션을 확인한 뒤 같은 환경·프로젝트에
새 이미지 태그를 배포합니다. `docker-smoke` 후 브라우저에서 실제 로그인·토큰 갱신,
사용 중인 이메일·OAuth·결제 콜백과 SSE를 검증합니다. healthcheck는 외부 사용자 흐름까지
증명하지 않습니다.

실패하면 상태·최근 로그를 확인합니다. 인프라와 데이터는 보존되지만 이전 API는 이미
교체됐을 수 있습니다. 스키마 호환성을 확인한 후에만 이전 `APP_IMAGE`를 선택하고
`DEPLOY_SOURCE=pull` 또는 `local`로 재배포하세요. 호환되지 않는 마이그레이션은 쓰기를
중지한 상태에서 검증된 백업 복구 절차를 따릅니다. 이미지 버전만 무작정 내리지 마세요.
배포 명령은 DB를 자동 복원하거나 볼륨을 삭제하지 않습니다.

`make docker-down`은 선택한 프로젝트를 중지하고 기본적으로 이름 있는 볼륨은 남깁니다.
일반 업데이트에 쓰는 명령은 아닙니다. 모든 핵심 명령은 선택한 환경 파일과 Compose
오버레이 목록을 유지합니다. [Compose 파일 선택](https://docs.docker.com/compose/how-tos/environment-variables/envvars/)을 참고하세요.

## 개발 모드 후원 링크

선택한 Docker 환경파일에 `VITE_BUY_ME_A_COFFEE_ENABLED=true`, `VITE_BUY_ME_A_COFFEE_URL=https://buymeacoffee.com/yourname`을 설정하고 `make docker-deploy`로 다시 빌드합니다. 기본값은 꺼짐이며 두 값은 비밀값이 아닌 공개 빌드 인자입니다. B4A 홈과 사이드바는 서버 `APP_MODE=development`에서만 링크를 표시하고 운영 모드에서는 설정과 무관하게 숨깁니다. 올바른 HTTPS 프로필 주소가 필요하며 외부 임베드는 추가하지 않습니다. Vite 빌드 시점 설정이므로 실행 환경만 바꾸거나 기존 이미지만 재시작해서는 반영되지 않습니다.

수동 Build 워크플로는 GHCR 이미지의 공개 프론트 빌드 인자로 `coffee_enabled`(기본 false), `coffee_url`을 받습니다. 서버 운영 모드에서는 이 설정과 무관하게 후원 링크가 숨겨집니다. 머지 후 `ref=main`, `publish_image=true`로 실행하면 `manual-main` 태그가 갱신됩니다.


## 공개 관리자 데모

`docker/.env`에 `DEMO_ENABLED=true`를 설정하고 기능이 포함된 이미지로 `make docker-deploy DEPLOY_SOURCE=pull`을 실행합니다. 기본값은 `false`이며 운영 모드에서도 사용할 수 있습니다. 런타임 설정이라 프론트엔드 이미지를 다시 빌드할 필요가 없고 `/config`의 `demo_enabled`로 확인할 수 있습니다.

비로그인 방문자도 프로필 드롭다운의 **관리자 패널 (데모)** 또는 홈 미리보기에서 `/demo/admin`, `/demo/admin/server`로 접근합니다. 기존 관리자 화면을 재사용하며 조회 전용 `/api/v1/admin/demo/users`, `/api/v1/admin/demo/status`를 호출합니다. 실제 관리자 API의 권한 검사는 유지됩니다.

활성화하면 실제 사용자 수·역할·활성/인증 여부·로그인 제공자·UTC 일 단위 가입/최근 로그인 날짜와 서버 상태·기능 활성 상태가 공개됩니다. 이름·이메일·DB 식별자는 키 기반 가명으로 대체하고 내부 연결 호스트·포트는 제거합니다. 검색도 가명만 대상으로 합니다. 소수 집단에서는 역할 등으로 추정할 여지가 있는 가명화 데이터입니다. 자격 증명·IP·프로필 데이터와 변경 API는 공개하지 않습니다. 결과는 프로세스별 최대 30초 캐시하며 오류 시 원본 데이터로 대체하지 않습니다. 최초 사용자 스냅샷은 전체 사용자의 최소 필드를 조회하므로 대규모 운영에서는 메모리 사용량을 점검한 뒤 사용합니다.

`DEMO_ENABLED=false`로 재배포하면 메뉴가 사라지고 데모 API는 404를 반환합니다. 가명을 바꾸려고 `SECRET_KEY`를 변경하지 마세요. 인증 토큰에도 사용하는 키입니다. 데모 활성화는 메트릭·트레이싱·로그 내보내기 또는 옵저버빌리티 스택을 켜지 않습니다.
