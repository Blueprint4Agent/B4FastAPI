# 마이그레이션 롤포워드 런북

이 런북은 롤포워드 우선 정책으로 마이그레이션 실패를 처리하는 방법을 정의합니다.
공유 환경 및 운영 환경에서는 기본적으로 다운그레이드를 수행하지 않습니다.

## 1) 사전 조건

1. 현재 대상 DB 및 연결 설정 확인
2. 마이그레이션 작업 전 DB 백업 수행
3. 현재 revision/head 상태 확인

## 2) 기준 상태 점검

`src/backend`에서 실행:

```bash
uv run alembic current
uv run alembic history --verbose
```

## 3) 실패 분류

1. Revision 메타데이터 이슈:
- revision 네이밍 오류, 깨진 `down_revision`, 중복 revision
2. DDL 충돌:
- 테이블/컬럼/인덱스가 이미 존재하거나 누락
3. 데이터 마이그레이션 이슈:
- 제약조건/타입/길이 위반
4. 운영 이슈:
- 권한, lock timeout, 연결성

## 4) 롤포워드 절차

1. 자동 배포 재시도 중지
2. 실패 상세 수집:
- 실패한 revision
- SQL/로그 스니펫
- 현재 revision (`alembic current`)
3. 전진 수정 적용:
- 마이그레이션 로직 보정 또는 보정용 migration revision 추가
4. 재실행:

```bash
uv run alembic upgrade head
```

5. 검증:
- 기대 스키마 상태
- startup 로그의 migration 완료
- 핵심 API 스모크 테스트

## 5) 가드 규칙

1. Revision id 형식: `NNNN_snake_case`
2. Revision id 최대 길이: `32`
3. 운영에 이미 적용된 revision 삭제 금지
4. 데이터 마이그레이션은 추가적(additive)이고 가능하면 idempotent 하게 작성

## 6) 예시: Revision 길이 실패

증상:
- `alembic_version.version_num`에서 `value too long for type character varying(32)` 발생

조치:
1. 문제 revision id를 32자 이하로 축약
2. 이를 참조하는 하위 revision 파일의 `down_revision` 업데이트
3. 재빌드/재배포 후 `alembic upgrade head` 실행
