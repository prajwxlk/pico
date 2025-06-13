import network
import urequests
import time
from machine import Pin, SPI
import st7789py as st7789  # Your provided ST7789 module

# WiFi credentials
SSID = "Airtel_Home"
PASSWORD = "kadbane@home"

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print(".", end="")
    print("\nConnected:", wlan.ifconfig())

# Setup ST7789 display
spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
display = st7789.ST7789(
    spi, 240, 240,
    reset=Pin(12, Pin.OUT),
    dc=Pin(8, Pin.OUT),
    cs=Pin(9, Pin.OUT),
    backlight=Pin(13, Pin.OUT)
)
display.init()
display.backlight.on()

# Helper to wrap long text
def wrap_text(text, width=28):
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line + word) < width:
            line += word + " "
        else:
            lines.append(line.strip())
            line = word + " "
    if line:
        lines.append(line.strip())
    return lines

# Show the quote on screen
def show_quote(text, author):
    display.fill(st7789.WHITE)
    display.rect(0, 0, 240, 240, st7789.BLACK)
    display.hline(0, 20, 240, st7789.BLUE)
    display.vline(5, 20, 220, st7789.BLUE)

    lines = wrap_text(text)
    y = 30
    for line in lines:
        display.text(line, 10, y, st7789.BLACK)
        y += 20
    display.text(f"- {author}", 10, y + 10, st7789.GREEN)

# Run
connect_wifi()
display.fill(st7789.WHITE)
display.text("Fetching quote...", 20, 100, st7789.BLUE)

try:
    res = urequests.get("https://api.quotable.io/random")
    data = res.json()
    quote = data.get("content", "No content")
    author = data.get("author", "Anonymous")
    res.close()
    show_quote(quote, author)
except Exception as e:
    print("Error:", e)
    display.fill(st7789.WHITE)
    display.text("API fetch error", 30, 110, st7789.RED)