import socket
import sys
import time
from config import TCP_PORT
from protocol import create_text_packet

# 請填入接收端電腦的正確 IPv4 位址
SERVER_IP = "192.168.1.4"  

def main():
    print(f"[1/4] 開始執行，目標伺服器: {SERVER_IP}:{TCP_PORT}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    try:
        print("[2/4] 正在嘗試建立 TCP 連線...")
        sock.connect((SERVER_IP, TCP_PORT))
        print("[3/4] 連線成功！正在打包並傳送文字封包...")

        pkt = create_text_packet("測試訊息：Hello from Client!", frame_id=1)
        sock.sendall(pkt)
        print(f"[4/4] 傳送完畢！已送出 {len(pkt)} bytes")

        # 稍微暫停 0.5 秒，確保 TCP 緩衝區資料送達伺服端後再關閉連線
        time.sleep(0.5)

    except socket.timeout:
        print("[錯誤] 連線逾時 (Timeout)：接收端防火牆阻擋，或 IP/Port 錯誤！")
    except ConnectionRefusedError:
        print("[錯誤] 連線被拒絕 (Refused)：接收端的 Server 程式未啟動，或 Port 填錯！")
    except Exception as e:
        print(f"[錯誤] 發生未預期異常: {type(e).__name__} - {e}")
    finally:
        sock.close()
        print("[*] 程式結束")

if __name__ == "__main__":
    main()