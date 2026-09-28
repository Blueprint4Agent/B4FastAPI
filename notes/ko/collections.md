# 검색과 페이지네이션 계약

## 백엔드 사용법

목록 라우터에서 `app.routers.list_query`의 `PageQuery`, `PageSizeQuery`, `SearchQuery`와 같은 모듈의 `DEFAULT_PAGE_SIZE`를 재사용합니다.

```python
page: PageQuery = 1,
page_size: PageSizeQuery = DEFAULT_PAGE_SIZE,
search: SearchQuery = "",
```

본문이 아닌 개별 쿼리 파라미터입니다. page는 1 이상, page_size는 1~100(기본 20), search는 최대 200자이며 잘못된 값은 422입니다. 기존 계약처럼 길이 검증 후 서비스에서 앞뒤 공백을 제거합니다. 빈 검색어는 검색 조건을 추가하지 않습니다. 임의로 자르지 않습니다.

이름 있는 도메인 응답은 `PageResponse[DomainItemResponse]`를 상속하고 필요한 summary를 추가합니다. `items`, `total`, `page`, `page_size`를 공유하면서 관리자 스키마 이름과 평면 JSON을 유지합니다. 프론트엔드는 생성 타입을 사용하고 수동으로 복제하지 않습니다.

검색 필드와 정렬은 저장소가 소유합니다. 문자 그대로의 부분 검색은 `Users.list_admin_users`처럼 `icontains(search, autoescape=True)`를 사용하여 `%`, `_`를 와일드카드로 해석하지 않습니다. 대소문자 비교는 DB/콜레이션에 따르며 모든 유니코드 동등성을 보장하지 않습니다. 개수와 행 조회에 동일한 권한/필터 조건을 적용합니다. 고유 키로 동률을 해소하는 정렬(관리자는 ID 내림차순) 후 `(page - 1) * page_size` offset과 limit을 적용합니다. 개수 계산·페이지 처리를 위해 전체 행을 읽지 않습니다. 요청 간 고정 스냅샷은 보장하지 않습니다.

범위 밖 페이지는 빈 `items`, 실제 필터 적용 `total`, 요청한 `page`를 반환합니다. UI는 성공 응답 후 보정해 재요청할 수 있습니다. 빈 결과는 404가 아닌 200입니다. 목록 조회 전에 권한을 확인하고 전체 통계는 필터된 건수와 구분해 표시합니다.

계속 증가하는 목록은 서버 페이지네이션을 사용합니다. 커서 방식은 별도 계약이 필요하며 이번 offset 도구 범위 밖입니다. 기존 API 키는 개수 상한 없이 전체 목록을 반환하는 호환성 예외입니다. 별도 API 변경에서 공급자·고정 소비자 계약·생성 타입을 함께 전환해야 합니다.

## 프론트엔드 사용법

고정된 프론트엔드의 [한국어 가이드](../../src/frontend/notes/ko/collections.md), [영문 가이드](../../src/frontend/notes/collections.md)에 `useCollectionQuery`, `useClientPagination`, `getPagination`과 연결 예제가 있습니다. 서버 검색은 기본 제출 방식, 로컬 카탈로그는 즉시 검색을 사용합니다. 검색 적용·필터·페이지 크기 변경 시 1페이지로 돌아갑니다. 알 수 없는 total로 로딩 중 페이지를 보정하지 않습니다. 요청 취소·이전 계정 응답 차단·데스크톱/실시간 복구는 도메인 훅에 유지합니다.

## 검증

루트 `make check`, `make test`를 실행합니다. `make contract-check`로 공개·고정 OpenAPI 스키마가 바뀌지 않았는지 확인합니다. 관리자 통합 테스트는 기본값·범위·문자 검색·공백 제거·권한·빈 결과/범위 밖 페이지를, 프론트엔드 테스트는 쿼리 전환·로컬 목록 축소/초기화·요청/렌더 격리를 검증합니다.
