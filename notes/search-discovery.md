# Search discovery and publication

[한국어](ko/search-discovery.md)

Blueprint4Agent (B4A) is the umbrella project. Blueprint4FastAPI (B4FastAPI) combines
FastAPI with pinned B4React: authentication, typed API contracts and a repeatable
workflow for agents and developers. Describe integrations as configuration-dependent;
see [publication evidence](publication.md). Do not promise production certification,
security audits, indexing or AI recommendations.

## Public pages and build

Keep the existing app at /home. The optional /about/ and /about/ko/ introductions
contain static English/Korean content, setup commands, screenshots and documentation
links. They reuse home styling and remain readable without JavaScript. App pages
are noindex in this mode; only the public introduction URLs enter sitemap.xml.
Canonical/hreflang describe the two languages. robots.txt allows search crawlers
and blocks GPTBot/ClaudeBot. This policy is not authentication or universal training
exclusion. The public manifest contains content hashes for IndexNow change detection.

Local default-brand development serves both /about/ paths at the normal Vite origin,
without a separate preview port or build. Development pages are noindex and omit
canonical links. Custom identity builds do not publish B4A introduction content.

For a source-built server, after merging and updating the checkout/submodule, set
these public build values in docker/.env:

```dotenv
VITE_PUBLIC_DISCOVERY=true
VITE_PUBLIC_SITE_URL=https://blueprint4agent.org
```

Run `make docker-check` and `make docker-deploy` using the existing Compose overlays.
The default deployment builds an image, updates containers and checks readiness.
Do not run a second redundant build. For prebuilt images, use the manual Build
workflow's public_site_url/public_discovery inputs, publish the reviewed revision,
and deploy that exact image through the existing image/pull workflow. A container
restart alone does not change compiled HTML. Generic downstream projects must not
enable B4A-specific publication; use their own public content instead.

After deployment verify real HTTP 200 HTML at /about/ and /about/ko/, text/plain at
/robots.txt and XML at /sitemap.xml. Check canonical origin, reciprocal language
links, screenshot/CSS loading and anonymous access. Missing /about/ URLs and static
files must remain 404, even with Accept: text/html, rather than SPA fallback. Existing
/home, /login and extension-free application routes retain their fallback.

## IndexNow (optional, disabled by default)

Generate a public ownership key (for example `python3 -c 'import uuid; print(uuid.uuid4().hex)'`).
Set VITE_INDEXNOW_KEY in docker/.env and rebuild. This key is intentionally public,
not an API credential. The built /<key>.txt must return that same value.

First inspect a dry run against the deployed origin:

```bash
python3 scripts/indexnow.py --origin https://blueprint4agent.org --key YOUR_PUBLIC_KEY
```

Add `--submit` to submit manually. Set `INDEXNOW_ENABLED=true` in docker/.env to
invoke the same submission after successful `make docker-deploy` smoke checks.
It downloads the deployed manifest, compares it with docker/.indexnow/accepted.json,
validates sitemap/key/canonical pages and submits only added, changed or deleted
public URLs. Removed URLs must return 404/410. HTTP 200/202 advances the local
accepted-submission state, not an indexing ledger; failures preserve it for retry.
No changes means no request. Keep the state for subsequent deployments; losing it
causes the current public URLs to be treated as new. Use a separate --state path
per origin. A notification failure fails the command after deployment; it does not
roll back healthy containers. Retry the submission command after resolving it.
No automatic push, PR, scheduled Actions or Google Indexing API calls are added.

## Registration and verification

1. Confirm the canonical HTTPS origin and publicly reachable pages before submission.
2. Google Search Console: select the existing domain property and submit the full
   sitemap URL. Review URL inspection/indexing separately from submission success.
3. Bing Webmaster Tools: use the existing website and submit the sitemap; IndexNow
   is supplemental. Observe Search Performance and AI Performance separately.
4. Naver Search Advisor: use the actual HTTPS site, complete its current HTML-file
   or homepage-meta verification, then submit the sitemap. Do not reuse verification
   values from a different property without checking. RSS is optional when a real
   feed exists; do not fabricate one for a two-page introduction.
5. Check real verified-bot requests in WAF/server logs. A locally forged User-Agent
   returning 200 does not establish that the provider's IPs can access the site.
   Limit any WAF exception to documented bot identity/IPs; keep other protections.

Observed on 2026-10-12 before rollout: Google and Bing properties were present;
Google had zero submitted sitemap rows. Naver had an HTTP entry awaiting ownership
verification. Public robots.txt and sitemap.xml returned 404. These are dated
observations, not completed deployment/submission claims.

## Content, outreach and measurement

Prioritize a working quick start, identity/feature boundaries, typed-contract and
auth/deployment explanations before a broad blog tree. Link GitHub README to the
public introduction only after the URL is live. Relevant repository topics include
fastapi, python, react, typescript, boilerplate and developer-tools; never infer
search ranking from a topic change. [Outreach drafts](outreach-drafts.md) are for
review, not evidence that anything was posted. Check each community's rules before
posting; Show HN needs something people can actually try.

Track a weekly baseline: search impressions/clicks, public-page visits, GitHub
outbound clicks where analytics is explicitly configured, clone/traffic aggregates
and voluntarily reported adoption. Stars/forks are interest signals, not active
users. No telemetry SDK or user tracking is enabled by this change.

For ChatGPT/Claude/Perplexity record date, search-enabled mode, exact query and
actual citation URLs for (a) B4A name lookup, (b) general FastAPI recommendations,
(c) official-source citations. A single answer is not a stable rank or coverage
measure. Keep crawler access, indexing, recommendation, click and adoption distinct.

## Official references

- [Google Sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google JavaScript SEO](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Localized URLs](https://developers.google.com/search/docs/specialty/international/localized-versions)
- [OpenAI bots](https://developers.openai.com/api/docs/bots)
- [Anthropic bots](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)
- [Perplexity bots](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)
- [IndexNow protocol](https://www.indexnow.org/documentation)
- [Naver sitemap/RSS](https://searchadvisor.naver.com/guide/request-feed)
- [Show HN](https://news.ycombinator.com/showhn.html)
