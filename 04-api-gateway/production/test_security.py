import urllib.request
import json
import time

BASE_URL = "http://localhost:8000"

def run_test():
    print("--- 1. Test GET /health (Public) ---")
    try:
        res = urllib.request.urlopen(f"{BASE_URL}/health")
        print("Status:", res.status)
        print("Response:", res.read().decode())
    except Exception as e:
        print("Failed:", e)

    print("\n--- 2. Test POST /ask (Không có Token - Expected 401) ---")
    req = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps({"question": "Hello Agent"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print("Status:", e.code)
        print("Response:", e.read().decode())

    print("\n--- 3. Đăng nhập lấy JWT Token (student / demo123) ---")
    login_data = json.dumps({"username": "student", "password": "demo123"}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/auth/token",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    token = ""
    try:
        res = urllib.request.urlopen(req)
        resp_body = json.loads(res.read().decode())
        token = resp_body["access_token"]
        print("Token lấy thành công (20 kí tự đầu):", token[:20])
    except Exception as e:
        print("Đăng nhập thất bại:", e)
        return

    print("\n--- 4. Gửi câu hỏi POST /ask hợp lệ (Có Token - Expected 200) ---")
    req = urllib.request.Request(
        f"{BASE_URL}/ask",
        data=json.dumps({"question": "Hi, what is Docker?"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    try:
        res = urllib.request.urlopen(req)
        print("Status:", res.status)
        print("Response:", res.read().decode())
    except Exception as e:
        print("Thất bại:", e)

    print("\n--- 5. Spam 12 requests liên tiếp để kích hoạt Rate Limiting (Expected 429) ---")
    for i in range(12):
        req = urllib.request.Request(
            f"{BASE_URL}/ask",
            data=json.dumps({"question": f"Spam {i}"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        try:
            res = urllib.request.urlopen(req)
            print(f"Request {i+1}: Success (200) - Remaining requests: {json.loads(res.read().decode())['usage']['requests_remaining']}")
        except urllib.error.HTTPError as e:
            print(f"Request {i+1}: Failed ({e.code}) - {e.read().decode().strip()}")
            break

if __name__ == "__main__":
    run_test()
