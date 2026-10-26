import struct


# ============================================================
# Protocol Settings
# ============================================================

MAGIC = 0x4652414D   # ASCII: "FRAM"


VERSION = 1

TYPE_FRAME = 0x01
TYPE_TEXT = 0x02

PIXEL_FORMAT_BGR24 = 0x02
PIXEL_FORMAT_GRAY8 = 0x01
PIXEL_FORMAT_RGB24 = 0x03   # 標準 RGB 排列
     # 純文字封包

# ============================================================
# Packet Structure
# ============================================================

HEADER_FORMAT = "<IBBIHHBI"
# Header 格式
#
# <    = Little Endian
# I    = uint32  MAGIC
# B    = uint8   VERSION
# B    = uint8   TYPE
# I    = uint32  FRAME_ID
# H    = uint16  WIDTH
# H    = uint16  HEIGHT
# B    = uint8   PIXEL_FORMAT
# I    = uint32  PAYLOAD_SIZE
#
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

CRC_SIZE = 4

# ============================================================
# TCP Settings
# ============================================================

TCP_PORT = 5000

# ============================================================
# Video Settings
# ============================================================

# 每秒取幾幀
SAMPLE_FPS = 10

# ============================================================
# Video Settings
# ============================================================

# 每秒取幾幀
SAMPLE_FPS = 10

# ============================================================
# Frame Settings
# ============================================================

MAX_FRAME_ID = 0xFFFFFFFF
MAX_WIDTH = 0xFFFF
MAX_HEIGHT = 0xFFFF
MAX_PAYLOAD_SIZE = 0xFFFFFFFF