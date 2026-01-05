import os
import time
import requests

BASE = os.environ.get('BASE_URL','http://127.0.0.1:8001')

def main():
    register_url = f"{BASE}/api/auth/register"
    login_url = f"{BASE}/api/auth/login"
    me_url = f"{BASE}/api/auth/me"

    payload = {"username": "ci_test_user", "password": "pass123"}
    try:
        r = requests.post(register_url, json=payload, timeout=10)
        print('REGISTER', r.status_code)
        print(r.text)
    except Exception as e:
        print('REGISTER ERROR', e)
        return

    # Try login
    try:
        r = requests.post(login_url, json=payload, timeout=10)
        print('LOGIN', r.status_code)
        print(r.text)
        if r.status_code != 200:
            return
        data = r.json()
        token = data.get('token')
    except Exception as e:
        print('LOGIN ERROR', e)
        return

    # Call me endpoint
    try:
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get(me_url, headers=headers, timeout=10)
        print('ME', r.status_code)
        print(r.text)
    except Exception as e:
        print('ME ERROR', e)

if __name__ == '__main__':
    # small delay to let server start
    time.sleep(1)
    main()
