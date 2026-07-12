# 정책한눈 PolicyBrief G2C

`Policybrief-G2C`는 정부의 주요 정책·브리핑 자료를 수집해 시민이 읽기 쉬운 뉴스레터 초안으로 만드는 Python 기반 MVP입니다. 기본 실행은 오프라인 데모와 로컬 미리보기 중심이며, 실제 이메일 발송은 비활성화되어 있습니다.

## 주요 기능

- RSS 및 설정 기반 HTML 수집기
- 공통 `PolicyDocument` 스키마와 SQLite 저장소
- 텍스트 정제, 정확·유사 중복 제거
- 키워드 기반 정책 분야 분류
- 투명한 중요도 점수 산정
- 외부 API 없이 동작하는 추출식 요약기
- 선택형 OpenAI 호환 LLM 요약기와 실패 시 자동 대체
- Jinja2 기반 HTML/텍스트 뉴스레터 생성
- 안전 기본값의 SMTP 발송 추상화

## 아키텍처

```mermaid
flowchart LR
  A["공식 출처 설정"] --> B["RSS/HTML 수집"]
  B --> C["PolicyDocument 정규화"]
  C --> D["정제·중복 제거"]
  D --> E["분류·중요도 산정"]
  E --> F["요약 생성"]
  F --> G["뉴스레터 렌더링"]
  G --> H["로컬 검토"]
  H --> I["선택적 이메일 발송"]
```

## 설치

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## 데모 실행

외부 네트워크나 API 키 없이 가상 정책 자료로 뉴스레터를 생성합니다.

```bash
policybrief run --demo
```

결과 HTML과 텍스트 파일은 `data/newsletters/` 아래에 저장됩니다. 반복 실행해도 같은 문서와 같은 이슈 ID로 갱신됩니다.

## 설정

`.env.example`을 참고해 `.env`를 만들 수 있습니다. 실제 비밀번호, API 키, 구독자 목록은 Git에 저장하지 않습니다.

출처 설정은 `config/sources.example.yaml` 형식입니다. 실제 운영 전에는 출처 도메인, 선택자, robots/이용정책, 공공저작물 이용 조건을 직접 검증해야 합니다.

## CLI

```bash
policybrief collect
policybrief process
policybrief summarize
policybrief build-newsletter
policybrief preview
policybrief send --dry-run
policybrief run --demo
policybrief validate-config
policybrief show-stats
```

`send`는 기본적으로 dry-run입니다. 실제 발송은 `EMAIL_SEND_ENABLED=true`와 `--confirm-send`가 모두 있어야 하며, SMTP와 수신자 설정이 없으면 거부됩니다.

## 선택형 LLM

기본 요약기는 외부 API를 쓰지 않습니다. LLM을 쓰려면 다음 값을 설정합니다.

```env
SUMMARY_PROVIDER=llm
LLM_ENABLED=true
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=...
```

수집된 원문은 신뢰할 수 없는 데이터로 취급하며, LLM 프롬프트는 원문 안의 명령을 따르지 않도록 분리합니다.

## 선택형 SMTP

```env
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
EMAIL_SEND_ENABLED=false
```

수신자는 `EMAIL_RECIPIENTS` 또는 Git에서 제외된 `subscribers.txt`로 로드합니다. 로그에는 전체 주소 목록을 남기지 않습니다.

## 테스트와 품질 검사

```bash
ruff check .
ruff format --check .
mypy src
pytest --cov=policybrief_g2c
```

GitHub Actions도 같은 검사를 실행합니다.

## 저장소 구조

```text
config/                 출처·분류 설정
data/                   로컬 DB와 생성 뉴스레터
docs/                   운영·구조 문서
src/policybrief_g2c/    애플리케이션 코드
tests/                  오프라인 테스트와 데모 fixture
```

## 보안과 개인정보

- 출처 도메인 allowlist 검증
- 요청 timeout, retry, 과도한 수집 방지
- HTML 출력 자동 escaping
- 비밀값과 구독자 목록 Git 제외
- 이메일 발송 비활성화 기본값
- 원문 링크와 기관, 발행일 보존
- 삭제·정정·보존 정책은 운영 문서에 따라 확장

## 로드맵

MVP:

- RSS 및 범용 HTML 수집
- 결정론적 분류
- 추출식 요약
- 로컬 뉴스레터 생성
- 검토 우선 워크플로

향후:

- 검증된 정부 Open API 연동
- 출처별 전용 어댑터
- 구독자 관심사 관리
- 의미 검색과 대시보드
- 다국어 요약
- 사람 승인 워크플로
- 개인정보 보호형 발송 분석
- 정정·철회 워크플로

## 한계와 고지

현재 `config/sources.example.yaml`의 URL과 선택자는 예시입니다. 실제 정부 사이트에 적용하기 전 수동 검증이 필요합니다.

이 뉴스레터는 공식 공개 자료를 자동 요약한 초안입니다. 원문 게시물이 최종적이고 권위 있는 출처이며, 세부 내용은 변경될 수 있습니다. 자격, 기한, 절차는 원문 또는 담당 기관을 통해 반드시 확인하세요.
