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
