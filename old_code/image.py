from machine import Pin, SPI
import st7789

# --- SPI Setup for Waveshare 1.3" ST7789 ---
spi = SPI(1, baudrate=40000000, polarity=1, phase=1,
          sck=Pin(10), mosi=Pin(11))

tft = st7789.ST7789(
    spi, 240, 240,
    reset=Pin(12, Pin.OUT),
    dc=Pin(8, Pin.OUT),
    cs=Pin(9, Pin.OUT),
    backlight=Pin(13, Pin.OUT)
)

# --- Initialize display ---
tft.init()
tft.fill(0)  # Clear screen to black

# --- Show image.raw ---
try:
    with open("image.raw", "rb") as f:
        for y in range(240):
            row = f.read(240 * 2)
            if not row:
                break
            tft.blit_buffer(row, 0, y, 240, 1)
    print("Image display complete.")
except Exception as e:
    print("Failed to load image:", e)