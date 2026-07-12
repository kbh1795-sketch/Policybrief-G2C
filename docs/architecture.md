# Architecture

PolicyBrief G2C는 `collect -> process -> summarize -> build newsletter` 파이프라인으로 동작한다.

## Components

- Collectors: `RSSCollector`, `HTMLCollector`가 allowlist 검증 후 원문을 수집한다.
- Models: `PolicyDocument`와 `NewsletterIssue`가 추적 가능한 공통 스키마를 제공한다.
- Storage: SQLite 저장소가 문서, 중복 관계, 이슈, 발송 이력을 보관한다.
- Processing: 정제, 중복 제거, 키워드 분류, 중요도 점수 산정을 수행한다.
- Summarization: 기본은 추출식 요약이며, 설정 시 LLM 요약을 사용할 수 있다.
- Newsletter: Jinja2 템플릿으로 HTML과 plain text를 렌더링한다.

## Importance Formula

중요도는 0~100점으로 정규화한다.

- 최신성: 최대 25점, 발행 후 경과일에 따라 지수 감소
- 기관 우선순위: 최대 10점
- 전국 적용 가능성: 최대 15점
- 신청·마감 존재: 최대 10점
- 직접 시민 영향: 최대 20점
- 법·금융·제도 효과: 최대 10점
- 원문 완결성: 최대 10점
- 신규성: MVP에서는 기본 10점

각 구성 점수는 `metadata.importance_components`에 저장해 감사 가능성을 유지한다.

## Safety

수집 문서는 untrusted data로 취급한다. LLM 사용 시 원문은 명확히 구분하고, 원문 내부 명령을 따르지 않도록 시스템 지시를 둔다. HTML은 Jinja2 autoescape를 사용한다.
