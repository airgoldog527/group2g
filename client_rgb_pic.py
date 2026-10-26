import cv2

from config import TCP_PORT, REMOTE_IP
from protocol import create_frame_packet, PIXEL_FORMAT_BGR24
from transport import TCPTransport

IMAGE_PATH = "image/test.jpg"
FRAME_ID = 1


def main():
    # 讀取彩色圖片
    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print("圖片讀取失敗！請檢查 image/test.jpg")
        return

    height, width = image.shape[:2]

    # 保留彩色 BGR 資料
    payload = image.tobytes()

    # 建立彩色封包
    packet = create_frame_packet(
        frame_id=FRAME_ID,
        width=width,
        height=height,
        payload=payload,
        pixel_format=PIXEL_FORMAT_BGR24
    )

    print("準備傳送彩色圖片")
    print("圖片尺寸：", width, "x", height)
    print("封包大小：", len(packet), "bytes")

    transport = TCPTransport(REMOTE_IP, TCP_PORT)

    try:
        transport.connect()
        transport.send(packet)
        print("彩色圖片傳送成功！")
    except OSError as e:
        print("傳送失敗：", e)
    finally:
        transport.close()


if __name__ == "__main__":
    main()