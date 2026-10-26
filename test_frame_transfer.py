import threading
import time
import struct

import cv2

from protocol import (
    create_frame_packet,
    parse_frame_packet,
    HEADER_SIZE,
    CRC_SIZE,
    PIXEL_FORMAT_GRAY8
)

from transport import TCPTransport

from config import TCP_PORT,HEADER_FORMAT, SAMPLE_FPS

# ============================================================
# Test Settings
# ============================================================

HOST = "127.0.0.1"

IMAGE_PATH = "image/test.jpg"

FRAME_ID = 1


# ============================================================
# Server
# ============================================================

def server():
    print("[Server] 伺服器已啟動，等待連線...")
    
    # 建立監聽連線
    server_transport = TCPTransport(HOST, TCP_PORT)
    client_transport = None

    try:
        client_transport = server_transport.listen()
        print("[Server] 傳送端已連線，開始接收 Header...")

        # 1. 先接收固定長度的 Header
        header = client_transport.receive_exactly(HEADER_SIZE)

        # 2. 從 Header 中解包取得 Payload Size (使用 config 的格式)
        fields = struct.unpack(HEADER_FORMAT, header)
        frame_id = fields[3]
        width = fields[4]
        height = fields[5]
        pixel_format = fields[6]
        payload_size = fields[7]

        print("\n[Server] 收到 Header 資訊：")
        print(f"  Frame ID     : {frame_id}")
        print(f"  Width        : {width}")
        print(f"  Height       : {height}")
        print(f"  Pixel Format : {pixel_format}")
        print(f"  Payload Size : {payload_size} bytes")

        # 3. 依照 Header 的長度接收 Payload 和 CRC
        remaining_size = payload_size + CRC_SIZE
        remaining = client_transport.receive_exactly(remaining_size)

        # 4. 組回完整 Packet 並呼叫自訂協定解析
        packet = header + remaining
        frame = parse_frame_packet(packet)
        
        print("[Server] Packet 協定與 CRC32 校驗成功！")

        # 5. 將二進位資料（Bytes）還原為 NumPy 灰階矩陣
        payload = frame["payload"]
        received_image = np.frombuffer(
            payload, 
            dtype=np.uint8
        ).reshape(
            frame["height"], 
            frame["width"]
        )

        # 6. 儲存收到的影像，以便用肉眼檢查
        output_path = "received_frame.jpg"
        cv2.imwrite(output_path, received_image)
        print(f"[Server] 影像已還原並儲存至：{output_path}")

    except Exception as e:
        print(f"[Server] 發生錯誤：{e}")
        
    finally:
        # 安全關閉 Socket 連線
        if client_transport is not None:
            client_transport.close()
        server_transport.close()
        print("[Server] 伺服器關閉。")


# ============================================================
# Client (發送端)
# ============================================================
def client():
    print("[Client] 啟動發送任務...")

    # 1. 讀取測試圖片
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        raise FileNotFoundError(
            f"找不到圖片：{IMAGE_PATH}，請確認 image 資料夾與圖片是否存在。"
        )

    # 2. 彩色轉灰階（對齊原測試規格）
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    print("\n[Client] 準備發送影像：")
    print(f"  Image Size : {width} × {height}")

    # 3. 將 NumPy 矩陣拉平成原始 bytes
    payload = gray.tobytes()

    # 4. 建立符合專案協定的 Frame Packet
    packet = create_frame_packet(
        frame_id=FRAME_ID,
        width=width,
        height=height,
        payload=payload,
        pixel_format=PIXEL_FORMAT_GRAY8
    )

    print(f"  Payload    : {len(payload)} bytes")
    print(f"  Packet     : {len(packet)} bytes")

    # 5. 建立 TCP 連線並發送
    transport = TCPTransport(HOST, TCP_PORT)
    
    try:
        print("[Client] 正在連線至本地伺服器...")
        transport.connect()
        print("[Client] 連線成功，開始傳送完整封包...")
        
        transport.send(packet)
        print("[Client] Packet 傳送完成。")
        
    except OSError as e:
        print(f"[Client] 傳送失敗：{e}")
        
    finally:
        transport.close()
        print("[Client] 傳送端關閉。")


# ============================================================
# Main (主程式控制流)
# ============================================================
def main():
    print("========================================")
    print("       Frame Transfer Test ")
    print("========================================")
    print(f"系統設定偵測：連接埠={TCP_PORT}, FPS限制={SAMPLE_FPS}")

    # 1. 建立並啟動 Server 背景線程
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True  # 設定為守護線程，主程式結束時會自動關閉
    server_thread.start()

    # 2. 稍微等待讓 Server 綁定 Port 並進入監聽狀態
    time.sleep(0.3)

    # 3. 在主線程執行 Client 發送
    try:
        client()
    except Exception as e:
        print(f"[Main] Client 執行失敗: {e}")

    # 4. 等待 Server 線程處理完畢
    server_thread.join(timeout=5)

    print()
    print("========================================")
    print("      Frame Transfer Test PASSED!")
    print("========================================")


if __name__ == "__main__":
    main()