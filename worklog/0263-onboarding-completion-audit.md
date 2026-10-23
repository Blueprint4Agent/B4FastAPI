# Commit Title

feat(onboarding): project.json 기반 설정 대체와 초기화 감사 보강

# Changed File Scope

AGENTS.md, PROJECT_ONBOARDING.md, 새 PROJECT_ONBOARDING_AUDIT.md 및 대응 한국어 문서, README/PROJECT_SETUP의 완료 기준 안내를 변경합니다. 추가 요청에 따라 공통 설정 fallback을 보완하는 scripts/project_identity.py, backend startup_display.py와 사용자 환영 알림, 관련 테스트와 B4React pin도 변경합니다. Test 전용 설정은 생성하지 않습니다.

# Reason

초기화 트리거 확인용 실행은 실제 Test 서비스를 만드는 작업이 아니었습니다. 시험 적용을 롤백하고 다음 초기화에서 UI의 고정 로고, favicon, 환영 알림, 콘솔 배너, 문서, 이미지와 언어 설정이 누락되지 않도록 전체 표면 목록과 완료 근거를 먼저 관리해야 합니다.

# Design

초기화 의도/적용 대상 판별 → 단계별 수집 → 변경 전 소스/표면 인벤토리와 복구 기록 → 적용 → 잔여 이름 감사 → 실제 동작 검증 → 완료 판정 순서를 명시합니다. 별도 스킬 없이 AGENTS.md가 절차와 필수 감사표로 연결합니다. 리허설은 격리 복제본에서 수행하고 원본 env/소스/서브모듈/외부 저장소에 적용하지 않습니다. 감사표는 실제 프로젝트 안에서 채우며 필수 항목의 누락/미해결 상태가 있으면 완료로 판정하지 않습니다.

# Verification Plan

롤백 후 부모/자식 작업 트리와 원래 pin을 확인하고 backend/docker env를 자동 백업과 바이트 단위로 대조합니다. 시험 생성 설정/아이콘/브리프/워크로그를 제거하고 기본 프론트엔드 빌드를 복구합니다. 이후 문서 변경에 대해 루트 make verify-plan → make verify와 링크/한영 지침 동등성/시나리오 점검을 수행합니다. 새로운 실제 프로젝트 초기화나 런타임 수정은 하지 않습니다.

# Impact

실제 초기화와 트리거 리허설을 구분합니다. 기존 make init/project-init 진입점은 유지하며 manifest에 선택 필드 default_language=en|ko를 추가합니다. 기존 manifest와 기본 브랜드는 호환됩니다. 원본 식별자/출처 URL은 보존 이유를 기록하고 사용자 노출 서비스명·아이콘과 구분합니다. 미변경 구현까지 검사한 경우 이유와 결과 재사용 여부를 기록하며 검증기 자체의 최적화는 별도 작업으로 남깁니다.

# Loop Alignment

설정이 없을 때 기존 브랜드/브라우저 언어 동작을 유지하고 있을 때 공개 브랜드 설정/기존 EMAIL_BRAND_NAME을 사용합니다. 백엔드 request/event/task의 흐름은 보존하며 같은 생성 트랜잭션의 알림 문구와 lifespan 표시만 수정합니다. 프론트엔드 API/realtime/desktop recovery 루프는 변경하지 않으며 UI composition은 기존 공용 컴포넌트를 재사용합니다. 실제 초기화에서 해당 루프 검토는 계속 필수이며 적용/검증 근거를 감사표와 워크로그에 기록합니다.

# Verification

- Test 시험 적용의 부모/자식 소스 변경을 모두 롤백했습니다. 자식 pin은 원래 dd010e3073f60cc83ffdd7da445cda838147c668입니다.
- backend/docker env는 .project-backups/20261023T122757920068Z의 적용 전 백업과 바이트 단위로 일치합니다. 기존 frontend .env는 수정하지 않았습니다.
- Test project.json, 임시 아이콘, 생성된 project.local.json/logo.svg, Test 브리프/작업 기록과 시험용 자식 소스를 제거했습니다. 기존 블루프린트 프론트엔드 빌드 복구가 통과했습니다. 원래 빌드 출력의 바이트 동일성은 보관하지 않았으므로 주장하지 않습니다.
- 시험 결과에는 기본 브랜드 가정, 동일한 표시명/짧은 이름의 중복 요소 검색, 사용자 정의 프로젝트에서 원본 공개 소개를 기대하는 테스트 문제가 있었습니다. 소스 수정 대신 향후 초기화의 수용 시나리오로 반영합니다.
- 최종 공통 구현에 대한 루트 make verify-plan/make verify(run-pjhr609t)는 backend+branding+deployment+discovery+frontend-app+governance, frontend=full을 선택했고 13개 명령을 135.0초에 통과했습니다. 이는 이번 한 번의 관찰값입니다.
- 백엔드 504건, 초기화 11건, 프론트엔드 212건, UI 253건, 기본 프로덕션 18건과 격리 사용자 지정 프로젝트의 212건/프로덕션 18건이 통과했습니다. 계약/패키징과 도구/문서 검사도 통과했습니다. 기존 런타임 연동/운영 배포/네이티브 패키징은 변경 범위 밖이라 실행하지 않았습니다.
- 온보딩/감사 진입 문서의 상대 링크 118개가 유효합니다. 한영 표면 목록·기본/설정 override·리허설/롤백 시나리오를 검토했습니다. 감사 문서는 자동 시각 검증 보장이 아닌 에이전트 실행 의무임을 명시했습니다.
- 실제 변경 전에는 기존 검사도 소스/문서/환경 전체 fingerprint 변경으로 여러 번 실행됐습니다. 최종 계획의 초기화 검사도 backend/branding 두 명령 그룹에 포함되어 있습니다. 검증기를 수정하거나 불명확한 범위를 수동 축소하지 않았으며 캐시 개선은 별도 작업으로 남깁니다.
- Test 전용 파일 부재 및 원본 env 백업 일치를 최종 구현 후에도 확인했습니다. 이후 커밋/PR의 거버넌스와 pre-push 재검증은 동일 내용의 결과 재사용을 따릅니다.

## 추가 요청: 공통 설정 fallback

readProjectConfig()/__PROJECT_BRAND__를 그대로 재사용하고 설정 존재 시 브랜드/기본 언어를 대체합니다. 백엔드는 기존 EMAIL_BRAND_NAME을 사용합니다. 원본 workspace에 Test 설정을 다시 적용하지 않으며 사용자 지정 이름·아이콘·한국어 기본값은 격리된 기존 project-build-test에서 검증합니다. 실제 소스 변경에 맞는 루트 Make 범위를 실행하며 검증기 최적화는 섞지 않습니다.

- B4React PR #100을 merge commit으로 병합했고 부모 pin을 085b4ec07a2bf35e074750001434f93ad48745c0로 갱신했습니다. 자식 actual PR governance와 pre-push가 통과했으며 8개 명령 결과를 0.9초에 재사용했습니다.
