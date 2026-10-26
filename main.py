import cv2
import numpy as np
import struct

from config import TCP_PORT
from protocol import (
    parse_frame_packet,
    HEADER_SIZE,
    HEADER_FORMAT,
    CRC_SIZE,
    PIXEL_FORMAT_BGR24
)
from transport import TCPTransport


def main():
    # 監聽所有網路介面
    server = TCPTransport("0.0.0.0", TCP_PORT)
    client = None

    try:
        client = server.listen()
        print("已連線，等待彩色影片封包...")
        print("按 q 可以關閉接收畫面")

        while True:
            # 先接收固定長度的 Header
            header = client.receive_exactly(HEADER_SIZE)

            fields = struct.unpack(HEADER_FORMAT, header)
            payload_size = fields[7]

            # 再依照 Header 的長度接收 Payload 和 CRC
            body = client.receive_exactly(
                payload_size + CRC_SIZE
            )

            packet = header + body
            frame = parse_frame_packet(packet)

            if frame["pixel_format"] != PIXEL_FORMAT_BGR24:
                print("收到的不是彩色封包，略過。")
                continue

            image = np.frombuffer(
                frame["payload"],
                dtype=np.uint8
            ).reshape(
                frame["height"],
                frame["width"],
                3
            )

            cv2.imshow("Received Color Video", image)

            print(
                f"收到 Frame {frame['frame_id']}，"
                f"大小：{frame['width']} × {frame['height']}"
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n接收端停止。")

    except (ConnectionError, OSError, ValueError) as e:
        print("接收中斷：", e)

    finally:
        if client is not None:
            client.close()

        server.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()