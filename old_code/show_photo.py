# Web interface to upload and resize image in browser (client-side)
# Save this HTML on your Pico or serve it through your MicroPython server

html = """
<!DOCTYPE html>
<html>
  <head>
    <title>Upload Image</title>
    <style>
      body { font-family: Arial; margin: 40px; }
    </style>
  </head>
  <body>
    <h1>Upload Image for Display</h1>
    <input type="file" accept="image/*" onchange="handleImageUpload(event)">
    <canvas id="canvas" width="240" height="240" style="display: none;"></canvas>
    <script>
      function handleImageUpload(event) {
        const file = event.target.files[0];
        const img = new Image();
        const reader = new FileReader();
        reader.onload = function(e) {
          img.src = e.target.result;
        };
        img.onload = function() {
          const canvas = document.getElementById('canvas');
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, 240, 240);
          canvas.toBlob(function(blob) {
            const formData = new FormData();
            formData.append("image", blob, "resized.bmp");
            fetch("/upload", {
              method: "POST",
              body: formData
            }).then(res => alert("Uploaded successfully!"));
          }, 'image/bmp');
        };
        reader.readAsDataURL(file);
      }
    </script>
  </body>
</html>
"""

# MicroPython server-side code (for Raspberry Pi Pico W)
import network, socket, time, os
from machine import Pin, PWM, SPI
import framebuf

# Configure WiFi
ssid = 'Airtel_Home'
password = 'kadbane@home'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    print("Connecting...")
    time.sleep(1)
print("Connected:", wlan.ifconfig())

# Setup LCD Display
class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240
        self.cs = Pin(9, Pin.OUT)
        self.rst = Pin(12, Pin.OUT)
        self.dc = Pin(8, Pin.OUT)
        self.spi = SPI(1, baudrate=100000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11))
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([data]))
        self.cs(1)

    def init_display(self):
        self.rst(1)
        self.rst(0)
        self.rst(1)
        for cmd, val in [
            (0x36, 0x70), (0x3A, 0x05), (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33]),
            (0xB7, 0x35), (0xBB, 0x19), (0xC0, 0x2C), (0xC2, 0x01),
            (0xC3, 0x12), (0xC4, 0x20), (0xC6, 0x0F),
            (0xD0, [0xA4, 0xA1]), (0xE0, [0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]),
            (0xE1, [0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23])
        ]:
            self.write_cmd(cmd)
            if isinstance(val, list):
                for d in val: self.write_data(d)
            else:
                self.write_data(val)
        self.write_cmd(0x21)
        self.write_cmd(0x11)
        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        for d in [0x00, 0x00, 0x00, 0xef]: self.write_data(d)
        self.write_cmd(0x2B)
        for d in [0x00, 0x00, 0x00, 0xef]: self.write_data(d)
        self.write_cmd(0x2C)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

    def display_bmp(self, path):
        with open(path, "rb") as f:
            bmp = f.read()
            if bmp[0:2] != b"BM":
                print("Not BMP")
                return
            offset = int.from_bytes(bmp[10:14], "little")
            width = int.from_bytes(bmp[18:22], "little")
            height = int.from_bytes(bmp[22:26], "little")
            bpp = int.from_bytes(bmp[28:30], "little")
            if width != 240 or height != 240 or bpp != 24:
                print("Invalid size or depth")
                return
            pixel_data = bmp[offset:]
            i = 0
            for y in range(240):
                for x in range(240):
                    b = pixel_data[i]
                    g = pixel_data[i+1]
                    r = pixel_data[i+2]
                    color = ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3)
                    self.pixel(x, 239 - y, color)
                    i += 3
            self.show()

LCD = LCD_1inch3()

# Web server
def start_server():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Listening on", addr)

    while True:
        cl, addr = s.accept()
        print("Client connected from", addr)
        request = cl.recv(1024)
        request = request.decode('utf-8')
        print("Request:", request)

        if "POST /upload" in request:
            body = request.split('\r\n\r\n', 1)[1]
            with open("image.bmp", "wb") as f:
                f.write(body.encode())
            LCD.display_bmp("image.bmp")
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nImage received")
        else:
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            cl.send(html)
        cl.close()

start_server()