# run.py

import socket
import subprocess
import sys
import os
import time
import webbrowser

def find_free_port(start=8501, end=8600):
    """
    start부터 end까지 순서대로 사용 가능한 포트를 찾아 반환.
    모두 사용 중이면 None 반환.
    """
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return None

def get_local_ip():
    """
    외부로 나가는 UDP 소켓을 8.8.8.8:80에 연결해보면서
    로컬 머신의 LAN IP를 추출해서 반환.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 임의의 외부 주소(예: 구글 DNS)에 연결 시도
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        # 문제가 생긴다면 fallback으로 localhost 리턴
        return "127.0.0.1"

def main():
    python_cmd = sys.executable  # python 실행 경로 (예: C:\Users\LG\AppData\Local\…\python.exe)

    # 1) 사용 가능한 포트 찾기
    port = find_free_port(8501, 8600)
    if port is None:
        print("❌ 8501-8600 포트 중 비어 있는 포트를 찾을 수 없습니다.")
        return

    # 2) Streamlit 서버 실행 (백그라운드)
    cmd = [
        python_cmd, "-m", "streamlit", "run", "main.py",
        "--server.address", "0.0.0.0",
        "--server.port", str(port),
        "--server.headless", "true"
    ]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print("❌ Streamlit 실행 중 오류 발생:", e)
        return

    # 3) 잠깐 대기한 후 (Streamlit 서버가 켜질 시간을 줌)
    time.sleep(2)

    # 프로세스 상태 확인
    if process.poll() is not None:
        # 프로세스가 이미 종료됨
        stdout, stderr = process.communicate()
        print("❌ Streamlit 프로세스가 종료되었습니다.")
        print("STDOUT:", stdout.decode('utf-8'))
        print("STDERR:", stderr.decode('utf-8'))
        return

    # 4) 로컬 및 네트워크 URL 계산
    local_url   = f"http://localhost:{port}"
    lan_ip      = get_local_ip()
    network_url = f"http://{lan_ip}:{port}"

    # 5) 사용자에게 접속 주소 출력
    print("\n───────────────────────────────────")
    print(f"✅ Streamlit 앱이 실행 중입니다.")
    print(f"   로컬 접속:     {local_url}")
    print(f"   네트워크 접속: {network_url}")
    print("───────────────────────────────────\n")

    # 6) 기본 브라우저로 네트워크 URL 열기
    try:
        webbrowser.open(network_url, new=2)  # new=2: 새 탭 열기
    except Exception:
        print('브라우저 열기 실패')
        pass

    # 7) 프로세스가 종료될 때까지 대기
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 실행 중단. Streamlit 서버를 종료합니다.")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
    print('프로그램 종료')
