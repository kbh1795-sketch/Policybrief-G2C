# Source Policy

운영 출처는 명시적으로 설정한 공식 정부 도메인만 사용한다.

## Requirements

- `allowed_domains`에 포함된 호스트만 요청한다.
- 인증 우회, CAPTCHA 우회, 접근 제어 우회는 하지 않는다.
- robots 정책, 사이트 이용약관, 공공저작물 이용 조건을 확인한다.
- timeout, retry, request delay를 사용한다.
- 실패한 출처는 로그로 남기고 다른 출처 처리는 계속한다.
- 원문 제목, 기관, 발행일, URL, 수집 시각을 보존한다.

## Example Config

`config/sources.example.yaml`는 형식 예시다. 실제 URL과 CSS 선택자는 운영 전 수동 검증이 필요하다.

## Correction And Deletion

정정 요청이나 삭제 요청이 들어오면 SQLite에서 해당 문서 ID를 찾아 제거하거나 최신 원문으로 재수집한다. 향후 버전에서는 관리자 명령과 감사 로그를 추가한다.
