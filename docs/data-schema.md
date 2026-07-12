# Data Schema

## PolicyDocument

주요 필드:

- `id`: canonical URL, 발행일, 제목 기반 결정론적 ID
- `title`, `agency`, `source_name`, `source_type`
- `source_url`, `canonical_url`
- `published_at`, `collected_at`, `updated_at`
- `raw_text`, `clean_text`
- `summary`, `key_points`
- `citizen_impact`, `eligibility`, `application_method`
- `effective_date`, `deadline`
- `policy_category`, `keywords`, `importance_score`
- `content_hash`, `language`, `metadata`

## NewsletterIssue

- `id`: 제목과 대상 기간 기반 결정론적 ID
- `title`, `publication_date`
- `covered_start`, `covered_end`
- `documents`
- `generated_html`, `generated_text`
- `status`: `draft`, `reviewed`, `approved`, `sent`

## SQLite Tables

- `documents`: 문서 payload와 처리 상태
- `duplicate_relationships`: 대표 문서와 중복 URL
- `newsletter_issues`: 생성된 이슈 payload
- `send_history`: 실제 발송 기록
