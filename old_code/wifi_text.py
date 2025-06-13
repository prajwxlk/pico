from machine import Pin, SPI, PWM
import framebuf
import time
import network
import socket
import ure

BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240

        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)

        self.cs(1)
        self.spi = SPI(1, 100000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

        self.red = 0x07E0
        self.green = 0x001f
        self.blue = 0xf800
        self.white = 0xffff

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        self.rst(1)
        self.rst(0)
        self.rst(1)

        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A)
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35)

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F)

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        for val in [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54,
                    0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]:
            self.write_data(val)

        self.write_cmd(0xE1)
        for val in [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44,
                    0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23]:
            self.write_data(val)

        self.write_cmd(0x21)
        self.write_cmd(0x11)
        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)

        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)

        self.write_cmd(0x2C)

        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

    def draw_text_scaled(self, x, y, text, color, scale=2):
        for i, char in enumerate(text):
            for row in range(8):
                bits = ord(char) >> row
                for col in range(8):
                    if bits & (1 << col):
                        for dx in range(scale):
                            for dy in range(scale):
                                self.pixel(x + i*8*scale + col*scale + dx, y + row*scale + dy, color)

        self.show()

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    print("Connecting to WiFi...")
    while not wlan.isconnected():
        time.sleep(1)
        print("Connecting to WiFi...")
    print("Connected:", wlan.ifconfig())
    return wlan.ifconfig()[0]

def start_server(lcd):
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
    s.bind(addr)
    s.listen(1)
    print("Listening on", addr)

    while True:
        cl, addr = s.accept()
        print("Client connected from", addr)
        request = cl.recv(1024).decode()
        print("Request:", request)

        match = ure.search("GET /\\?text=([^ ]+)", request)
        text = ""
        if match:
            text = match.group(1).replace("+", " ")
            print("Text to display:", text)
            lcd.fill(lcd.white)
            lcd.draw_text_scaled(10, 100, text, lcd.blue, scale=2)

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "\r\n"
            "<!DOCTYPE html>\r\n"
            "<html>\r\n"
            "<head><title>LCD Input</title></head>\r\n"
            "<body>\r\n"
            "<h1>Enter text to display:</h1>\r\n"
            "<form action=\"/\" method=\"get\">\r\n"
            "<input type=\"text\" name=\"text\">\r\n"
            "<input type=\"submit\" value=\"Send\">\r\n"
            "</form>\r\n"
            "</body>\r\n"
            "</html>\r\n"
        )
        cl.send(response)
        cl.close()

if __name__ == '__main__':
    pwm = PWM(Pin(BL))
    pwm.freq(1000)
    pwm.duty_u16(32768)

    lcd = LCD_1inch3()
    lcd.fill(lcd.white)
    lcd.show()

    ip = connect_wifi("Airtel_Home", "kadbane@home")
    start_server(lcd)