from machine import Pin, SPI
import framebuf
import time

# Pin definitions
BL = 13    # Backlight
DC = 8     # Data/Command
RST = 12   # Reset
MOSI = 11  # SPI MOSI
SCK = 10   # SPI Clock
CS = 9     # Chip Select

class LCD_1inch3(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 240
        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)
        self.spi = SPI(1, baudrate=100_000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI))
        self.dc = Pin(DC, Pin.OUT)
        self.buffer = bytearray(self.height * self.width * 2)  # RGB565 = 2 bytes per pixel
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

        # Common color values
        self.red   = 0xf800
        self.green = 0x07e0
        self.blue  = 0x001f
        self.white = 0xffff
        self.black = 0x0000

    def write_cmd(self, cmd):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(bytearray([data]))
        self.cs(1)

    def init_display(self):
        self.rst(1); time.sleep(0.1)
        self.rst(0); time.sleep(0.1)
        self.rst(1); time.sleep(0.1)

        self.write_cmd(0x36); self.write_data(0x70)
        self.write_cmd(0x3A); self.write_data(0x05)
        self.write_cmd(0xB2)
        for d in (0x0C, 0x0C, 0x00, 0x33, 0x33): self.write_data(d)
        self.write_cmd(0xB7); self.write_data(0x35)
        self.write_cmd(0xBB); self.write_data(0x19)
        self.write_cmd(0xC0); self.write_data(0x2C)
        self.write_cmd(0xC2); self.write_data(0x01)
        self.write_cmd(0xC3); self.write_data(0x12)
        self.write_cmd(0xC4); self.write_data(0x20)
        self.write_cmd(0xC6); self.write_data(0x0F)
        self.write_cmd(0xD0); self.write_data(0xA4); self.write_data(0xA1)
        self.write_cmd(0xE0)
        for d in (0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23): self.write_data(d)
        self.write_cmd(0xE1)
        for d in (0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23): self.write_data(d)
        self.write_cmd(0x21)
        self.write_cmd(0x11); time.sleep(0.1)
        self.write_cmd(0x29); time.sleep(0.1)

    def show(self):
        self.write_cmd(0x2A)
        for d in (0x00, 0x00, 0x00, 0xEF): self.write_data(d)
        self.write_cmd(0x2B)
        for d in (0x00, 0x00, 0x00, 0xEF): self.write_data(d)
        self.write_cmd(0x2C)
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
