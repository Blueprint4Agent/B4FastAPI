# 검색 노출과 공개 절차

[English](../search-discovery.md)

Blueprint4Agent(B4A)는 상위 프로젝트 이름입니다. Blueprint4FastAPI(B4FastAPI)는
FastAPI와 고정 버전 B4React를 결합하여 인증, 타입 기반 API 계약, 에이전트와 개발자의
반복 가능한 개발 흐름을 제공합니다. 선택 연동은 별도 설정이 필요합니다.
[공개 근거](publication.md)에 따라 운영 인증·보안 감사·색인·AI 추천을 보장하지 않습니다.

## 공개 페이지와 빌드

기존 /home 앱을 유지하고 /about/(영어), /about/ko/(한국어)를 선택적으로 제공합니다.
정적 HTML에 기능, 설치 명령, 화면 이미지, 문서 링크를 넣어 JavaScript 없이도 읽을 수
있습니다. 홈 스타일을 재사용합니다. 이 모드에서 앱 페이지는 noindex이며 Sitemap은
소개 주소만 담습니다. canonical·hreflang으로 대표 주소와 언어 관계를 표시합니다.
robots.txt는 검색 봇을 허용하고 GPTBot·ClaudeBot은 차단합니다. 접근 제어나 모든 경로의
학습 방지 수단은 아닙니다. 공개 매니페스트는 IndexNow용 콘텐츠 지문을 담습니다.

기본 브랜드의 로컬 Vite 서버에서는 별도 포트나 빌드 없이 같은 /about/ 주소로 볼 수
있습니다. 개발 페이지에는 noindex를 적용하고 canonical을 생략합니다. 사용자 지정
브랜드에는 B4A 소개 페이지를 생성하지 않습니다.

변경 병합 후 서버에서 체크아웃과 서브모듈을 갱신하고 docker/.env에 지정합니다.

```dotenv
VITE_PUBLIC_DISCOVERY=true
VITE_PUBLIC_SITE_URL=https://blueprint4agent.org
```

기존 Compose 구성을 유지한 채 `make docker-check`, `make docker-deploy`를 실행합니다.
기본 배포는 이미지 빌드, 컨테이너 갱신, 정상 응답 확인까지 수행하므로 별도 중복 빌드는
필요하지 않습니다. GHCR 사전 빌드 이미지를 쓰면 수동 Build 워크플로의 public_site_url,
public_discovery 입력으로 검토한 리비전을 빌드·게시하고 기존 pull 배포 방식으로 해당
이미지를 적용합니다. 컨테이너 재시작만으로는 HTML이 바뀌지 않습니다. 파생 서비스는
B4A 공개 모드를 켜는 대신 자기 서비스의 공개 콘텐츠를 만들어야 합니다.

적용 후 /about/, /about/ko/의 실제 HTML 200 응답, /robots.txt의 text/plain,
/sitemap.xml의 XML, canonical 도메인, 언어 링크, CSS·이미지, 비로그인 접근을 확인합니다.
없는 /about/ 주소와 정적 파일은 Accept: text/html 요청에도 SPA 대신 404여야 합니다.
/home, /login 등 확장자가 없는 앱 경로는 기존 fallback을 유지합니다.

## IndexNow 선택 설정

기본값은 꺼짐입니다. `python3 -c 'import uuid; print(uuid.uuid4().hex)'` 등으로 공개 소유
확인값을 만들고 VITE_INDEXNOW_KEY에 넣어 재빌드합니다. API 비밀키가 아니며
/<key>.txt에 같은 값이 공개됩니다.

먼저 배포된 사이트를 대상으로 제출 없이 확인합니다.

```bash
python3 scripts/indexnow.py --origin https://blueprint4agent.org --key YOUR_PUBLIC_KEY
```

`--submit`을 붙이면 실제 제출합니다. docker/.env의 `INDEXNOW_ENABLED=true`는
`make docker-deploy` 정상 응답 검사 후 같은 제출 도구를 실행하게 합니다.
배포된 매니페스트와 docker/.indexnow/accepted.json을 비교하고 Sitemap·키·canonical을
검사한 뒤 추가·수정·삭제된 공개 URL만 보냅니다. 삭제 URL은 404/410이어야 합니다.
200/202는 제출 수락이며 색인 완료가 아닙니다. 수락 후만 로컬 기록을 갱신하고 실패 시
유지합니다. 변경이 없으면 제출하지 않습니다. 기록을 잃으면 현재 URL을 신규로 취급하므로
배포 간 유지하고, 다른 도메인은 별도 --state 경로를 사용합니다. 제출 실패는 이미 배포된
컨테이너를 되돌리지 않습니다. 원인을 해결하고 제출 명령만 재실행합니다.
자동 push·PR·예약 Actions나 Google Indexing API 호출은 추가하지 않습니다.

## 등록과 확인

1. 실제 HTTPS 대표 주소와 공개 페이지 접근을 확인합니다.
2. Google Search Console의 기존 도메인 속성에 전체 Sitemap URL을 제출합니다.
   제출 성공과 URL 검사·색인 결과를 구분합니다.
3. Bing의 기존 사이트에 Sitemap을 제출합니다. IndexNow는 보완 수단이며 검색 실적과
   AI 실적을 나눠 봅니다.
4. 네이버는 실제 HTTPS 주소로 등록하고 해당 화면의 HTML 파일 또는 홈페이지 메타태그로
   소유 확인한 뒤 Sitemap을 제출합니다. 다른 속성의 확인값을 확인 없이 재사용하지 않습니다.
   실제 피드가 있을 때만 RSS를 제출하며 소개 페이지를 위해 가짜 피드를 만들지 않습니다.
5. WAF·서버 로그에서 실제 검증된 봇의 접근을 확인합니다. 로컬에서 User-Agent만 바꿔
   200을 받았다고 제공업체 IP의 접근까지 검증한 것은 아닙니다. WAF 예외는 공식 봇 식별과
   IP 범위로 제한하고 다른 보호 규칙을 유지합니다.

2026-10-12 배포 전 확인: Google·Bing 속성이 존재했고 Google Sitemap 제출은 0건입니다.
네이버에는 HTTP 항목이 있으나 소유 확인 전입니다. 공개 robots.txt·sitemap.xml은 404였습니다.
이 기록은 당시 관찰이며 배포나 제출 완료를 의미하지 않습니다.

## 콘텐츠·홍보·측정

큰 블로그 구조보다 실제 실행 가능한 설치 가이드, 이름·기능·설정 범위, 타입 계약,
인증·배포 설명을 먼저 보강합니다. 소개 URL이 실제로 열린 뒤 README와 연결합니다.
Topics 후보는 fastapi, python, react, typescript, boilerplate, developer-tools이며
Topics 변경만으로 순위 상승을 판단하지 않습니다. [홍보 초안](outreach-drafts.md)은
검토용이며 게시 완료 기록이 아닙니다. 커뮤니티별 규정을 확인하고 Show HN에는 실제로
사용할 수 있는 결과물을 제출합니다.

주 단위로 검색 노출·클릭, 소개 방문, 명시적으로 설정한 분석 도구의 GitHub 이동 클릭,
집계된 clone·트래픽, 자발적으로 공유된 채택 사례를 구분합니다. Star·Fork는 관심도이며
실사용자 수가 아닙니다. 이번 변경은 추적 SDK나 사용자 수집을 활성화하지 않습니다.

ChatGPT·Claude·Perplexity 점검은 검색 활성화 여부, 날짜, 정확한 질문과 실제 인용 URL을
기록합니다. 이름 검색, 일반 FastAPI 추천, 공식 문서 인용을 나눠 봅니다. 한 번의 답변으로
고정 순위나 검색 범위를 판단하지 않습니다. 크롤링 허용·색인·추천·클릭·채택은 별개입니다.

## 공식 근거

- [Google Sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [언어별 URL](https://developers.google.com/search/docs/specialty/international/localized-versions)
- [OpenAI 봇](https://developers.openai.com/api/docs/bots)
- [Anthropic 봇](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)
- [Perplexity 봇](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)
- [IndexNow](https://www.indexnow.org/documentation)
- [네이버 Sitemap·RSS](https://searchadvisor.naver.com/guide/request-feed)
- [Show HN](https://news.ycombinator.com/showhn.html)

홈과 한글·영문 정적 About에서 프롬프트 만들기를 소개하고 `/prompt-builder`로 연결합니다. 소개는 자바스크립트 없이 읽을 수 있으며 작성기는 자바스크립트와 기존 앱 연결 확인이 필요합니다. 로컬 프롬프트 작성 기능이며 실제 저장소 분석·배포를 수행하지 않습니다.
