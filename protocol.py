# ---------- Packet Header ----------
import struct
import zlib


# ============================================================
# Frame Packet Protocol
# ============================================================

# ============================================================
# Frame Settings
# ============================================================

from config import (
    MAGIC,
    VERSION,
    TYPE_FRAME,
    TYPE_TEXT,
    PIXEL_FORMAT_GRAY8,
    HEADER_FORMAT,
    HEADER_SIZE,
    CRC_SIZE,
    MAX_FRAME_ID,
    MAX_WIDTH,
    MAX_HEIGHT,
    MAX_PAYLOAD_SIZE,
    PIXEL_FORMAT_BGR24
)

# ============================================================
# Create Packet
# ============================================================

def create_frame_packet(frame_id, width, height, payload,pixel_format=PIXEL_FORMAT_GRAY8):
    """
    建立一個 Frame Packet。

    Parameters
    ----------
    frame_id : int
        Frame 編號。

    width : int
        影像寬度。

    height : int
        影像高度。

    payload : bytes
        GRAY8 影像資料。

    Returns
    -------
    bytes
        完整 Frame Packet。
    """

    # --------------------------------------------------------
    # 檢查 Width / Height
    # --------------------------------------------------------

    if not (0 <= width <= MAX_WIDTH):
        raise ValueError(f"Width 超出範圍：{width}")

    if not (0 <= height <= MAX_HEIGHT):
        raise ValueError(f"Height 超出範圍：{height}")

    # --------------------------------------------------------
    # 檢查 Frame ID
    # --------------------------------------------------------

    if not (0 <= frame_id <= MAX_FRAME_ID):
        raise ValueError(f"Frame ID 超出範圍：{frame_id}")

    # --------------------------------------------------------
    # Payload 大小
    # --------------------------------------------------------

    payload_size = len(payload)

    if payload_size > MAX_PAYLOAD_SIZE:
        raise ValueError(
            f"Payload 太大：{payload_size} bytes (最大限制: {MAX_PAYLOAD_SIZE} bytes)"
        )

    # --------------------------------------------------------
    # 建立 Header
    # --------------------------------------------------------

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        TYPE_FRAME,
        frame_id,
        width,
        height,
        pixel_format,
        payload_size
    )

    # --------------------------------------------------------
    # 計算 Payload CRC32
    # --------------------------------------------------------

    crc = zlib.crc32(payload)

    crc_bytes = struct.pack(
        "<I",
        crc
    )

    # --------------------------------------------------------
    # Header + Payload + CRC
    # --------------------------------------------------------

    packet = header + payload + crc_bytes

    return packet


# ============================================================
# Parse Packet
# ============================================================

def parse_frame_packet(packet):
    """
    解析 Frame Packet。

    Parameters
    ----------
    packet : bytes
        完整 Frame Packet。

    Returns
    -------
    dict
        解析後的 Frame 資訊。
    """

    # 最小封包長度
    if len(packet) < HEADER_SIZE + CRC_SIZE:
        raise ValueError("Packet 太短")

    # --------------------------------------------------------
    # 解析 Header
    # --------------------------------------------------------

    header_data = packet[:HEADER_SIZE]

    (
        magic,
        version,
        packet_type,
        frame_id,
        width,
        height,
        pixel_format,
        payload_size
    ) = struct.unpack(
        HEADER_FORMAT,
        header_data
    )

    # --------------------------------------------------------
    # 驗證 Header
    # --------------------------------------------------------

    if magic != MAGIC:
        raise ValueError("MAGIC 錯誤")

    if version != VERSION:
        raise ValueError("VERSION 不支援")

    if packet_type != TYPE_FRAME:
        raise ValueError("Packet TYPE 錯誤")

    if pixel_format not in (PIXEL_FORMAT_GRAY8, PIXEL_FORMAT_BGR24):
        raise ValueError("Pixel Format 不支援")

    # --------------------------------------------------------
    # 取得 Payload
    # --------------------------------------------------------

    payload_start = HEADER_SIZE
    payload_end = payload_start + payload_size

    # 確認 Packet 是否完整
    expected_size = HEADER_SIZE + payload_size + CRC_SIZE

    if len(packet) != expected_size:
        raise ValueError(
            f"Packet 長度錯誤："
            f"實際 {len(packet)} bytes，"
            f"預期 {expected_size} bytes"
        )

    payload = packet[payload_start:payload_end]

    # --------------------------------------------------------
    # 取得 CRC
    # --------------------------------------------------------

    crc_start = payload_end
    crc_end = crc_start + CRC_SIZE

    received_crc = struct.unpack(
        "<I",
        packet[crc_start:crc_end]
    )[0]

    # --------------------------------------------------------
    # 驗證 CRC
    # --------------------------------------------------------

    calculated_crc = zlib.crc32(payload)

    if received_crc != calculated_crc:
        raise ValueError("CRC 檢查失敗")

    # --------------------------------------------------------
    # 回傳解析結果
    # --------------------------------------------------------

    return {
        "frame_id": frame_id,
        "width": width,
        "height": height,
        "pixel_format": pixel_format,
        "payload_size": payload_size,
        "payload": payload,
    }



# ============================================================
# Text Packet
# ============================================================

def create_text_packet(message, frame_id=0):
    """建立 UTF-8 純文字封包。"""

    if not isinstance(message, str):
        raise TypeError("message 必須是 str")

    if not isinstance(frame_id, int) or isinstance(frame_id, bool):
        raise TypeError("frame_id 必須是整數")

    if not (0 <= frame_id <= MAX_FRAME_ID):
        raise ValueError("Frame ID 超出範圍")

    payload = message.encode("utf-8")
    payload_size = len(payload)

    if payload_size > MAX_PAYLOAD_SIZE:
        raise ValueError("Payload 太大")

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        VERSION,
        TYPE_TEXT,
        frame_id,
        0,
        0,
        0,
        payload_size
    )

    crc = zlib.crc32(payload)

    return header + payload + struct.pack("<I", crc)


def parse_text_packet(packet):
    """解析 UTF-8 純文字封包。"""

    if len(packet) < HEADER_SIZE + CRC_SIZE:
        raise ValueError("Packet 太短")

    (
        magic,
        version,
        packet_type,
        frame_id,
        width,
        height,
        pixel_format,
        payload_size
    ) = struct.unpack(
        HEADER_FORMAT,
        packet[:HEADER_SIZE]
    )

    if magic != MAGIC:
        raise ValueError("MAGIC 錯誤")

    if version != VERSION:
        raise ValueError("VERSION 不支援")

    if packet_type != TYPE_TEXT:
        raise ValueError("不是文字封包")

    expected_size = HEADER_SIZE + payload_size + CRC_SIZE

    if len(packet) != expected_size:
        raise ValueError("Packet 長度錯誤")

    payload_end = HEADER_SIZE + payload_size
    payload = packet[HEADER_SIZE:payload_end]

    received_crc = struct.unpack(
        "<I",
        packet[payload_end:expected_size]
    )[0]

    if zlib.crc32(payload) != received_crc:
        raise ValueError("CRC 檢查失敗")

    return {
        "frame_id": frame_id,
        "payload_size": payload_size,
        "payload": payload,
        "message": payload.decode("utf-8"),
    }

# ============================================================
# Video Processing Module (新增：以模組函式方式整合影片抽幀與封包)
# ============================================================

def extract_and_packetize_video(video_path: str, sample_fps: int = 5, color_folder: str = "frames/color", gray_folder: str = "frames/gray") -> int:
    """
    開啟影片、定時抽幀，並建立對應的彩色與灰階 Frame Packet 儲存至本地。
    
    Parameters
    ----------
    video_path : str 影片檔案路徑。
    sample_fps : int 每秒抽取幾幀。
    color_folder : str 彩色封包儲存資料夾。
    gray_folder : str 灰階封包儲存資料夾。
    
    Returns
    -------
    int 成功處理的總幀數。
    """
    # 建立輸出資料夾
    os.makedirs(color_folder, exist_ok=True)
    os.makedirs(gray_folder, exist_ok=True)

    print(f"正在開啟影片: {video_path}...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"影片開啟失敗，請檢查路徑是否存在: {video_path}")
    
    print("影片開啟成功!")

    # 取得影片資訊
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_seconds = total_frames / source_fps if source_fps > 0 else 0

    print("\n===== 影片資訊 =====")
    print(f"原始 FPS: {source_fps}")
    print(f"總幀數: {total_frames}")
    print(f"影片長度: {video_seconds:.2f} 秒")
    print(f"抽取 FPS: {sample_fps}")
    print("====================")

    frame_id = 1
    sample_index = 0

    try:
        while True:
            # 計算這次要取得的原始影片 frame 編號
            target_frame = int(round(sample_index * source_fps / sample_fps))
            
            # 超過影片範圍就結束
            if target_frame >= total_frames:
                break

            # 移動到指定 frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret:
                print(f"警告：讀取影片第 {target_frame} 幀失敗，終止抽幀。")
                break

            height, width = frame.shape[:2]

            # 1. 彩色 Frame Packet (完全採用 config 統合之常數)
            color_payload = frame.tobytes()
            color_packet = create_frame_packet(
                frame_id=frame_id, width=width, height=height, 
                payload=color_payload, pixel_format=PIXEL_FORMAT_BGR24
            )
            color_path = os.path.join(color_folder, f"frame_{frame_id:04d}.bin")
            with open(color_path, "wb") as f:
                f.write(color_packet)

            # 2. 灰階 Frame Packet (完全採用 config 統合之常數)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_payload = gray.tobytes()
            gray_packet = create_frame_packet(
                frame_id=frame_id, width=width, height=height, 
                payload=gray_payload, pixel_format=PIXEL_FORMAT_GRAY8
            )
            gray_path = os.path.join(gray_folder, f"frame_{frame_id:04d}.bin")
            with open(gray_path, "wb") as f:
                f.write(gray_packet)

            print(f"Frame {frame_id}: 影片第 {target_frame} 幀 → 彩色 + 灰階封包儲存完成")
            
            frame_id += 1
            sample_index += 1
            
    finally:
        cap.release()

    processed_count = frame_id - 1
    print("\n================================")
    print("影片封包處理完成!")
    print(f"總共處理: {processed_count} 幀")
    print("================================")
    
    return processed_count

# ============================================================
# Image Conversion Module (新增：以模組函式方式整合影像還原與轉換)
# ============================================================

def packet_to_image(frame_dict: dict) -> np.ndarray:
    """
    將解析後的 frame 字典資料轉換為 NumPy 影像矩陣 (NDArray)。
    適用於即時顯示、影像處理或檔案儲存。
    """
    pixel_format = frame_dict["pixel_format"]
    width = frame_dict["width"]
    height = frame_dict["height"]
    payload = frame_dict["payload"]

    # 還原一維 byte 陣列
    img_buffer = np.frombuffer(payload, dtype=np.uint8)

    # 依據格式重新塑形 (Reshape)
    if pixel_format == PIXEL_FORMAT_BGR24:
        return img_buffer.reshape(height, width, 3)
    elif pixel_format == PIXEL_FORMAT_GRAY8:
        return img_buffer.reshape(height, width)
    else:
        raise ValueError(f"不支援的 Pixel Format，無法還原為影像: {pixel_format}")


def convert_bin_file_to_image_file(bin_path: str, output_image_path: str) -> dict:
    """
    讀取本地的 .bin 封包檔案，解析、還原並儲存為圖片檔案。
    
    Parameters
    ----------
    bin_path : str 本地二進位封包路徑。
    output_image_path : str 欲輸出的圖片路徑（如 .png, .jpg）。
    
    Returns
    -------
    dict 解析後的 Frame 資訊字典。
    """
    if not os.path.exists(bin_path):
        raise FileNotFoundError(f"找不到封包檔案: {bin_path}")

    # 1. 讀取二進位資料
    with open(bin_path, "rb") as f:
        packet_bytes = f.read()

    # 2. 呼叫內部解析函式
    frame_info = parse_frame_packet(packet_bytes)

    # 3. 轉換為 NumPy 矩陣
    image_mat = packet_to_image(frame_info)

    # 4. 寫入圖片檔案
    cv2.imwrite(output_image_path, image_mat)
    
    return frame_info


# ============================================================
# Stream Receiver / Buffer Manager
# ============================================================

class StreamReceiver:
    """
    接收端緩衝區管理器。
    為每一台連進來的電腦（無論是傳送文字或影像串流）各自建立一個實例，
    負責處理網路傳輸產生的「黏包」、「斷包/分包」與「雜訊對齊」。
    """

    def __init__(self):
        self._buffer = bytearray()
        # 取得 MAGIC 對應的 bytes 格式
        self._magic_bytes = struct.pack(HEADER_FORMAT[0] + "I" if HEADER_FORMAT[0] in "<>!=" else "<I", MAGIC)

    def feed(self, data: bytes):
        """將 socket.recv() 收到的位元組資料塞入暫存區"""
        if data:
            self._buffer.extend(data)

    def extract_packets(self):
        """
        嘗試從緩衝區切出所有已收齊的封包。
        以 Generator 依序 yield 解析後的封包 dict。
        """
        while True:
            # 1. 緩衝區長度不足以容納 Header 則跳出等待更多資料
            if len(self._buffer) < HEADER_SIZE:
                break

            # 2. 同步 MAGIC，防止封包前面夾帶雜訊或損毀位元
            idx = self._buffer.find(self._magic_bytes)
            if idx == -1:
                # 完全找不到 MAGIC，保留末端長度避免 MAGIC 被跨包切斷
                keep_len = len(self._magic_bytes) - 1
                del self._buffer[:-keep_len]
                break
            elif idx > 0:
                # 丟棄 MAGIC 之前的雜訊
                del self._buffer[:idx]
                if len(self._buffer) < HEADER_SIZE:
                    break

            # 3. 預讀 Payload Size
            header_data = bytes(self._buffer[:HEADER_SIZE])
            (
                _,
                _,
                _,
                _,
                _,
                _,
                _,
                payload_size,
            ) = struct.unpack(HEADER_FORMAT, header_data)

            total_packet_size = HEADER_SIZE + payload_size + CRC_SIZE

            # 4. 檢查整個封包是否已經接收完整
            if len(self._buffer) < total_packet_size:
                break

            # 5. 擷取完整封包並移出緩衝區
            raw_packet = bytes(self._buffer[:total_packet_size])
            del self._buffer[:total_packet_size]

            # 6. 解析並回傳
            try:
                yield parse_packet(raw_packet)
            except ValueError as err:
                # 遇 CRC 錯誤或未知格式時丟棄，繼續嘗試下一筆
                print(f"[StreamReceiver Warning] 無效封包已略過: {err}")