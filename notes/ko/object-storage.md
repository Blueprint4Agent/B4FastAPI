# 오브젝트 스토리지 프로바이더

`OBJECT_STORAGE_PROVIDER=local|s3|r2|supabase`로 저장소를 선택합니다.
사용자가 고르는 제공자는 네 가지이며, 원격 세 가지는 공통 S3 구현을 사용합니다.
설정은 중앙 `SETTINGS`에서 관리하고 `src/backend/.env.example`,
`docker/.env.example`에 선택지와 설명을 제공합니다. 기존 실제 `.env`는 변경하지 않습니다.
프로필 사진의 기존 Base64 저장은 아직 유지되며, 이번 단계는 #108의 백엔드 기반입니다.

## 설정

| 변수 | 의미 |
| --- | --- |
| `OBJECT_STORAGE_PROVIDER` | 기본 `local`, AWS/기타 S3는 `s3`, Cloudflare는 `r2`, Supabase는 `supabase` |
| `OBJECT_STORAGE_LOCAL_ROOT` | 절대 경로. 환경변수가 비어 있으면 backend/data/object-storage |
| `OBJECT_STORAGE_MAX_BYTES` | put/get 최대 크기. 기본 8 MiB, 허용 1 byte–100 MiB |
| `OBJECT_STORAGE_TIMEOUT_SECONDS` | S3 연결/읽기별 제한. 기본 10초, 허용 1–120초 |
| `OBJECT_STORAGE_S3_BUCKET` | 미리 만든 버킷 이름. 원격 필수 |
| `OBJECT_STORAGE_S3_ENDPOINT_URL` | AWS는 빈 값, R2/Supabase는 S3 엔드포인트 필수 |
| `OBJECT_STORAGE_S3_REGION` | AWS/Supabase 리전 필수. R2는 항상 auto 사용 |
| `OBJECT_STORAGE_S3_ACCESS_KEY_ID` | S3 접근 키. R2/Supabase 필수 |
| `OBJECT_STORAGE_S3_SECRET_ACCESS_KEY` | 접근 키와 한 쌍인 비밀키 |
| `OBJECT_STORAGE_S3_SESSION_TOKEN` | 명시적 키 쌍 사용 시 선택적인 AWS 임시 토큰 |
| `OBJECT_STORAGE_S3_ADDRESSING_STYLE` | auto/path/virtual. auto는 R2/Supabase에서 path, S3에서 SDK auto |

로컬은 `OBJECT_STORAGE_PROVIDER=local`만으로 시작할 수 있습니다. Docker에서는
기본 `/var/lib/b4fastapi/objects`에 API와 Celery worker가 같은 named volume을 마운트합니다.
직접 경로를 지정할 때에는 절대 경로를 사용합니다.

AWS는 `s3`를 선택하고 버킷과 리전을 지정합니다. 엔드포인트는 비워 두고,
접근 키/비밀키를 모두 비우면 SDK의 역할·환경변수·프로필 자격 증명 경로를 사용합니다.

R2는 `r2`를 선택하고 `https://ACCOUNT_ID.r2.cloudflarestorage.com`, 버킷,
R2 S3 접근 키/비밀키를 지정합니다. 엔드포인트에는 버킷 경로를 넣지 않습니다.
버킷까지 붙여 넣으면 SDK가 버킷을 중복해서 요청하므로 시작 전에 설정 오류로 거부합니다. 리전은 `auto`, addressing 기본은 `path`입니다.

Supabase는 `supabase`를 선택하고 Storage 설정에서 S3 엔드포인트·리전·S3 키를
복사합니다. 엔드포인트 예시는 `https://PROJECT_REF.storage.supabase.co/storage/v1/s3`입니다.
**anon/service-role API 키는 S3 키가 아닙니다.** 사용자별 권한은 도메인 서비스에서
확인하며 서버용 S3 키를 브라우저에 전달하지 않습니다.

설정 예제 전체와 제공자별 복사 가능한 dotenv 블록은 [영문 가이드](../object-storage.md)를
참고합니다. 설정 변경 후 API를 재시작합니다. 개발용 에뮬레이터만 HTTP를 허용하고,
운영 엔드포인트에는 HTTPS가 필요합니다. TLS 검증은 활성 상태로 유지합니다.

## 아키텍처와 계약

`core/object_storage/`에서 공통 `ObjectStorage`, `ObjectMetadata`, `StoredObject`,
`StorageError`를 제공합니다. 앱 lifespan이 인스턴스를 생성/종료하며 후속 시작 단계
실패 시에도 정리합니다. `app/deps.py`의 `get_object_storage`로 도메인 서비스에 주입합니다.
워커는 `create_object_storage(SETTINGS)`와 `finally: close()`로 수명주기를 관리합니다.
라우터/모델에서 SDK를 직접 호출하지 않습니다.

- put: 바이트와 MIME type을 저장하고 키·크기·콘텐츠 타입을 반환합니다. 동일 키는 교체합니다.
- get/stat: 크기가 제한된 바이트+메타데이터 또는 메타데이터만 읽습니다.
- delete: 없는 객체 삭제는 성공합니다. 없는 버킷/권한 오류는 실패합니다. 버전 관리가
  켜진 버킷은 이전 버전·삭제 마커가 남을 수 있으므로 물리적 완전 삭제를 보장하지 않습니다.
- 키는 512자 이하 ASCII 경로 부분집합이며 절대 경로, `..`, 빈 구간, 역슬래시와
  퍼센트 인코딩은 거부합니다. MIME type은 파라미터 없는 255자 이하 문자열입니다.
  MIME 메타데이터는 실제 파일 내용 검증을 대신하지 않습니다.
- 오류는 INVALID_INPUT/NOT_FOUND/ACCESS_DENIED/UNAVAILABLE/TOO_LARGE/CORRUPT_OBJECT/CLOSED로
  정규화합니다. 도메인에서 기존 HTTP 예외로 변환하며 원격 오류 원문·본문·비밀값은 기록하지 않습니다.
- 동기 파일/SDK I/O는 Starlette 스레드 풀에서 실행합니다. S3는 최대 3회 시도하며
  연결/읽기별 timeout을 적용합니다. 전체 작업 deadline은 아니며 취소/timeout이 쓰기를
  되돌리지 않습니다. 같은 키의 동시 쓰기는 마지막 완료 결과가 남습니다.

공개 업로드·서명 URL·공개 URL·목록 조회·대용량 multipart·ACL·버킷 생성 API는 이번 범위에
추가하지 않습니다. 기본 비공개이며 향후 인증된 도메인 다운로드 경로를 통해 접근합니다.
원격 장애 때 로컬 fallback을 하지 않습니다. 서버 시작 시 `check_connection()`을 반드시
실행합니다. 로컬은 고유 임시 파일을 쓰고 읽어 내용이 일치하는지 확인한 다음 삭제합니다.
원격은 읽기 전용 HeadBucket 요청으로 기존 버킷 접근을 확인합니다. 성공은 INFO, 실패는
제공자와 정규화된 오류 코드만 ERROR 로그로 남깁니다. 비밀값·경로·엔드포인트·본문은 기록하지
않으며 실패하면 클라이언트를 닫고 서버 시작을 중단합니다.

HeadBucket은 버킷 접근 권한(AWS의 경우 일반적으로 s3:ListBucket)이 필요합니다.
성공해도 개별 객체의 쓰기/삭제 권한을 증명하지 않으므로 배포 전 별도 검증이 필요합니다.
원격 버킷에 테스트 파일을 쓰지는 않습니다. AWS 자격 증명 확인 중 역할/메타데이터 서버 요청이
발생할 수 있습니다. 팩토리를 직접 사용하는 워커는 필요하면 check_connection()을 명시적으로
호출합니다.

## 로컬 저장·운영

논리 키를 해시한 파일명으로 평면 저장합니다. 각 파일은 버전이 있는 private record로
4바이트 헤더 길이 + JSON 메타데이터 + 원본 바이트를 포함하며 Base64를 사용하지 않습니다.
임시 파일/fsync/atomic replace로 메타데이터와 본문을 함께 교체합니다. 객체 심볼릭 링크와
일반 파일이 아닌 항목은 읽지 않습니다. 루트와 상위 경로는 운영자만 수정할 수 있어야 합니다.
macOS/Linux POSIX 파일시스템을 대상으로 하며 적대적인 공유 디렉터리는 지원하지 않습니다.
atomic replace는 다중 호스트 잠금이나 전원 장애 내구성 전체를 보장하지 않습니다.

Docker의 `object_storage_data` 볼륨은 컨테이너 재생성 이후에도 유지되지만 `down -v` 등으로
볼륨을 지우면 파일도 사라집니다. 단독 워커도 같은 경로/볼륨을 사용해야 하며 로컬 볼륨은
서로 다른 서버 간 공유 저장소가 아닙니다. 파일과 DB를 별도로 백업하고 함께 복원합니다.
프런트 빌드 디렉터리나 컨테이너 임시 파일시스템에 업로드를 저장하거나 이 디렉터리를 공개
정적 경로로 마운트하지 않습니다.

제공자/버킷/경로 변경은 데이터를 자동 이전하지 않습니다. 후속 도메인은 안정적인 키와
저장 위치 식별자를 기록하고 만료 URL을 DB에 저장하지 않아야 합니다. 프로필 사진 연계 시
이미지 검증·새 키 생성·DB 실패 보상·동시 교체·이전 파일/탈퇴 파일 정리·기존 Base64와 OAuth
외부 URL 처리 정책을 별도로 정의해야 합니다.

## 검증 범위

임시 로컬 디렉터리와 실제 SDK의 Stubber로 저장/읽기/교체/삭제, 경로 이탈·손상·동시 쓰기,
크기·오류 정규화·응답 스트림 종료·설정과 DI 수명주기를 검증합니다. 실제 AWS/R2/Supabase
계정에 쓰기/삭제 검증은 하지 않았습니다. 사용자 설정 R2 버킷에는 읽기 전용 HeadBucket을
실행했습니다. 중복 버킷 경로를 수정한 뒤 접근 검증 성공, 실행 서버 시작 로그와 /ping 정상
응답을 확인했습니다. AWS/Supabase 실연결은 미실행입니다. 배포 전 전용 테스트 버킷에서
최소 권한으로 put/stat/get/delete를
확인해야 하며 mock 또는 생성 성공을 실연결 성공으로 표시하지 않습니다.

S3 호환은 ACL·버전 관리 등 모든 AWS 기능의 동일 지원을 뜻하지 않습니다.
[R2 호환성](https://developers.cloudflare.com/r2/api/s3/api/),
[Supabase 호환성](https://supabase.com/docs/guides/storage/s3/compatibility),
[Supabase 인증](https://supabase.com/docs/guides/storage/s3/authentication)을 참고합니다.

## 프로필 사진 연동과 방어 정책

`0015_profile_photo` 마이그레이션은 users.profile_photo에 객체 키와 저장 위치 지문을
기록합니다. 새 사진의 profile_image_url은 버전이 있는 비공개 API 경로입니다. 기존
Base64/OAuth 사진은 자동 이전하지 않고 계속 표시합니다. 배포 전 `make db-migrate`를
실행합니다. downgrade는 관리형 API URL을 비우고 참조 컬럼을 제거하며 파일은 남깁니다.

- PUT /api/v1/auth/me/photo: 인증된 바이너리 업로드. 스트림을 최대 8 MiB로 제한하고
  실제 PNG/JPEG/WebP/GIF 형식과 1,600만 화소 제한을 확인합니다. 방향을 보정하고 최대
  512px WebP 정지 이미지로 변환하며 메타데이터를 제거합니다.
- GET /api/v1/auth/me/photo?version=...: 현재 사용자 사진만 인증 후 반환합니다.
  private/no-store·nosniff를 적용하고 버킷 주소/비밀키를 노출하지 않습니다.
- DELETE /api/v1/auth/me/photo: DB 참조를 비운 뒤 기존 파일을 정리합니다. 반복 삭제는
  성공합니다. 기존 PATCH의 사진 쓰기(null 포함)는 422로 거부하며 이름/단축키 수정은 유지합니다.

프런트는 auth hook으로 파일 바이트를 전송하고 성공한 서버 상태만 반영합니다. 계정/사진 버전별
Blob URL 하나를 설정·사이드바에서 공유하고 교체/로그아웃 시 해제합니다. 늦게 도착한 이전
계정의 이미지 응답은 무시합니다. 읽기 장애는 기본 아바타로 처리하며 로그아웃시키지 않습니다.
기존 동의 기반 최근 계정 썸네일의 저장·만료 정책은 유지합니다.

**원격 장애 시 로컬 자동 저장은 넣지 않습니다.** 로컬 대체 저장은 백업과 달리 서버별 파일 분산,
복구 후 동기화, 삭제 일관성까지 필요합니다. 현재 프로필 사진 용도로는 복잡도가 과합니다.
[AWS의 fallback 검토](https://builder.aws.com/content/3EuS9Sakq7L3VLQIF3qzfMfke1Y/avoiding-fallback-in-distributed-systems),
[OWASP 업로드 지침](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)을 참고했습니다.

새 랜덤 키 저장 → DB 버전 비교 후 참조 교체 → 이전 파일 삭제 순서입니다. 저장 실패 시 기존
사진을 유지하고 동시 변경은 409로 거부한 뒤 실패한 업로드만 지웁니다. DB 오류 시 현재 참조를
다시 확인해 이미 커밋된 사진을 보상 삭제하지 않습니다. 응답만 유실된 경우 실제 저장은 끝났을
수 있으므로 새로고침으로 확인합니다. 파일 정리 실패는 키와 안전한 오류 코드만 기록하고 성공한
DB 변경을 되돌리지 않습니다. 탈퇴 트랜잭션이 마지막 사진 참조를 반환해 정리합니다.

저장 위치 변경은 지문으로 감지하며 다른 버킷/로컬 경로에서 같은 키를 읽거나 지우지 않습니다.
자동 이관은 없으므로 운영자가 이전 파일을 옮기거나 사진을 교체해야 합니다. 정리는 best effort이며
작업 큐/outbox 보장은 없습니다. 강제 종료·취소·장기 장애의 고아 파일은 로그와 DB 참조를 대조해
정리해야 합니다. 전체 profile-photos 접두사에 만료를 걸면 사용 중 사진도 삭제되므로 피합니다.
고아 파일량/삭제 SLA가 커질 때 durable 정리 큐를 추가하고, 별도 백업·보존은 제공자별 운영 정책으로
설정합니다. SDK 제한 재시도는 유지하며 503 업로드를 프런트에서 무한 재시도하지 않습니다.
트래픽 규모에 따른 사용자 요청 제한은 ingress에서 설정할 수 있습니다. 시작 검증 실패 시 서버를
중단하는 기존 정책은 유지하므로 저장소 장애 중 재시작은 실패합니다. 가용성 요구가 커지면
일시 장애만 허용하는 degraded startup 정책을 별도로 결정해야 합니다.

## 관리자 상태

관리자 전용 `/admin/status`에 스토리지 제공자, 연결 방식, 포트, 상태, 응답 시간 및 캐시된 확인 시각을 추가합니다. 로컬은 임시 파일 쓰기·읽기·삭제, 원격은 HeadBucket으로 확인하며 업로드 권한이나 버킷 공개 여부를 검증하지 않습니다. 기존 프로세스별 60초 캐시·동시 요청 공유·응답 시간 제한을 재사용합니다. 비밀키, 원본 오류, 계정/프로젝트 식별자, 엔드포인트 호스트/URL, 버킷명, 리전, 로컬 경로는 응답에서 제외합니다. 화면에는 제공자 아이콘, 연결 방식/포트, 기존 상태·응답 시간을 표시하며 행별 확인 설명·시각은 표시하지 않습니다. 공개 readiness나 백그라운드 작업은 변경하지 않습니다.
