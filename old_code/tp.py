import network
import socket
import time
from machine import Pin, SPI

class ST7789:
    def __init__(self):
        self.width = 240
        self.height = 240

        self.spi = SPI(1, baudrate=62500000, sck=Pin(10), mosi=Pin(11))
        self.dc = Pin(8, Pin.OUT)
        self.rst = Pin(12, Pin.OUT)
        self.cs = Pin(9, Pin.OUT)
        self.bl = Pin(13, Pin.OUT)

        self.reset()
        self.init_display()

    def reset(self):
        self.rst.value(1)
        time.sleep(0.1)
        self.rst.value(0)
        time.sleep(0.1)
        self.rst.value(1)
        time.sleep(0.1)

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([data]))
        self.cs.value(1)

    def init_display(self):
        for cmd, data in (
            (0x36, 0x70), (0x3A, 0x05), (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33]),
            (0xB7, 0x35), (0xBB, 0x19), (0xC0, 0x2C), (0xC2, 0x01),
            (0xC3, 0x12), (0xC4, 0x20), (0xC6, 0x0F), (0xD0, [0xA4, 0xA1]),
            (0xE0, [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C,
                    0x18, 0x0D, 0x0B, 0x1F, 0x23]),
            (0xE1, [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51,
                    0x2F, 0x1F, 0x1F, 0x20, 0x23]),
        ):
            self.write_cmd(cmd)
            if isinstance(data, list):
                for d in data:
                    self.write_data(d)
            else:
                self.write_data(data)

        self.write_cmd(0x21)  # Inversion ON
        self.write_cmd(0x11)  # Sleep out
        time.sleep(0.12)
        self.write_cmd(0x29)  # Display ON

        self.bl.value(1)  # Backlight ON

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        for v in [x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]:
            self.write_data(v)
        self.write_cmd(0x2B)
        for v in [y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]:
            self.write_data(v)
        self.write_cmd(0x2C)

    def fill_color(self, color):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.dc.value(1)
        self.cs.value(0)
        line = bytearray([color >> 8, color & 0xFF] * self.width)
        for _ in range(self.height):
            self.spi.write(line)
        self.cs.value(1)

# ==== Wi-Fi ====
SSID = "Airtel_Home"
PASSWORD = "kadbane@home"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting...", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(1)
    print("\nConnected:", wlan.ifconfig()[0])

def web_page(state):
    color = "#fff" if state == "ON" else "#000"
    return f"""<html><head><title>LCD</title></head>
<body style="background:{color}; text-align:center;">
<h2>LCD is {state}</h2>
<form><button name=state value=ON>ON</button>
<button name=state value=OFF>OFF</button></form>
</body></html>"""

# ==== Main ====
lcd = ST7789()
lcd.fill_color(0x0000)  # black at start

connect_wifi()
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("Server at http://%s/" % addr[0])

state = "OFF"

while True:
    cl, addr = s.accept()
    print("Client", addr)
    req = cl.recv(1024).decode()

    if "state=ON" in req:
        state = "ON"
        lcd.fill_color(0xFFFF)  # white
    elif "state=OFF" in req:
        state = "OFF"
        lcd.fill_color(0x0000)  # black

    html = web_page(state)
    cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    cl.send(html)
    cl.close()
