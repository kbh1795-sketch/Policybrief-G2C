# Operations

## Local Demo

```bash
policybrief run --demo
```

생성물은 `data/newsletters/`에 저장한다.

## Normal Run

1. `config/sources.example.yaml`을 복사해 실제 출처 설정을 만든다.
2. `.env`에서 `SOURCE_CONFIG_PATH`를 설정한다.
3. `policybrief validate-config`로 설정을 확인한다.
4. `policybrief run`으로 수집부터 뉴스레터 생성까지 실행한다.
5. HTML을 검토한 뒤 필요한 경우만 발송한다.

## Email Safety

실제 발송은 기본적으로 꺼져 있다.

```bash
policybrief send --issue-id ISSUE_ID --dry-run
policybrief send --issue-id ISSUE_ID --dry-run false --confirm-send
```

운영 환경에서는 발송 전 이슈 상태를 별도 승인 절차로 관리해야 한다.

## Retention Placeholder

MVP는 로컬 SQLite에 데이터를 보존한다. 운영 시에는 원문 보존 기간, 삭제 요청 처리, 로그 보존 기간, 백업 정책을 별도 문서화해야 한다.
