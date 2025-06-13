from machine import Pin, SPI
import time
import framebuf
from writer import Writer
from font8x8_basic import font as font_dict
from font import Font

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
        
        self.cs(1)
        self.spi = SPI(1, 100000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)
        
        # Initialize with a smaller buffer (one line at a time)
        self.buffer = bytearray(self.width * 2)  # Single line buffer (240 pixels * 2 bytes)
        super().__init__(self.buffer, self.width, 1, framebuf.RGB565)
        
        self.init_display()
        self._line = 0  # Track current line for partial updates
        
        self.red   = 0x07E0
        self.green = 0x001f
        self.blue  = 0xf800
        self.white = 0xffff
        self.black = 0x0000
        # Initialize font
        self.font = Font(font_dict, width=8, height=8)
        # Initialize writer with our display and font
        self.writer = Writer(self, self.font)
        # Set a default background color
        self.fill(self.white)
        # Update the display
        for _ in range(self.height):
            self.show()


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
        
    def show(self):
        """Update the display with the current buffer contents."""
        # Set the window to the current line
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)  # XS=0
        self.write_data(0x00)
        self.write_data(0xEF)  # XE=239
        
        self.write_cmd(0x2B)
        self.write_data((self._line >> 8) & 0xFF)
        self.write_data(self._line & 0xFF)  # YS=current line
        self.write_data((self._line >> 8) & 0xFF)
        self.write_data(self._line & 0xFF)  # YE=current line
        
        # Write the line data
        self.write_cmd(0x2C)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
        # Move to next line, wrap around if needed
        self._line = (self._line + 1) % self.height

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
        for d in [0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23]:
            self.write_data(d)

        self.write_cmd(0xE1)
        for d in [0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23]:
            self.write_data(d)
        
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
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
    def blit_raw_image(self, filename):
        try:
            with open(filename, "rb") as f:
                for y in range(self.height):
                    row = f.read(self.width * 2)  # 2 bytes per pixel (RGB565)
                    if not row:
                        break
                    self.write_cmd(0x2A)
                    self.write_data(0x00)
                    self.write_data(0x00)
                    self.write_data(0x00)
                    self.write_data(self.width - 1)

                    self.write_cmd(0x2B)
                    self.write_data(0x00)
                    self.write_data(y)
                    self.write_data(0x00)
                    self.write_data(y)

                    self.write_cmd(0x2C)
                    self.cs(1)
                    self.dc(1)
                    self.cs(0)
                    self.spi.write(row)
                    self.cs(1)
            print("Image loaded:", filename)
        except Exception as e:
            print("Failed to load image:", e)
            
    def fill(self, color):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data((self.width - 1) >> 8)
        self.write_data((self.width - 1) & 0xFF)

        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data((self.height - 1) >> 8)
        self.write_data((self.height - 1) & 0xFF)

        self.write_cmd(0x2C)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        
        # Fill with color - one line at a time
        self.fill_rect(0, 0, self.width, self.height, color)
        self.cs(1)

    def fill_rect(self, x, y, w, h, color):
        """Fill a rectangle with the specified color."""
        # Clip to display bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        
        if w <= 0 or h <= 0:
            return
            
        # Prepare color bytes (RGB565 format)
        color_hi = (color >> 8) & 0xFF
        color_lo = color & 0xFF
        
        # Set the window to the rectangle
        self.write_cmd(0x2A)
        self.write_data(x >> 8)
        self.write_data(x & 0xFF)
        self.write_data(((x + w - 1) >> 8) & 0xFF)
        self.write_data((x + w - 1) & 0xFF)
        
        self.write_cmd(0x2B)
        self.write_data(y >> 8)
        self.write_data(y & 0xFF)
        self.write_data(((y + h - 1) >> 8) & 0xFF)
        self.write_data((y + h - 1) & 0xFF)
        
        # Fill the rectangle
        self.write_cmd(0x2C)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        
        # Fill one line at a time
        for _ in range(h):
            # Fill one line with the color
            color_bytes = bytearray([color_hi, color_lo] * w)
            self.spi.write(color_bytes)
        
        self.cs(1)
    
    def rect(self, x, y, w, h, color):
        # Top and bottom
        for i in range(w):
            self.draw_pixel(x + i, y, color)
            self.draw_pixel(x + i, y + h - 1, color)
        # Left and right
        for i in range(h):
            self.draw_pixel(x, y + i, color)
            self.draw_pixel(x + w - 1, y + i, color)

    def draw_pixel(self, x, y, color):
        self.write_cmd(0x2A)
        self.write_data(x >> 8)
        self.write_data(x & 0xFF)
        self.write_data(x >> 8)
        self.write_data(x & 0xFF)

        self.write_cmd(0x2B)
        self.write_data(y >> 8)
        self.write_data(y & 0xFF)
        self.write_data(y >> 8)
        self.write_data(y & 0xFF)

        self.write_cmd(0x2C)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([color >> 8, color & 0xFF]))
        self.cs(1)
        
    def draw_char(self, ch, x, y, color):
        glyph = font.get(ch.upper(), font[' '])
        for row_idx, row in enumerate(glyph):
            for col in range(8):
                if (row >> (7 - col)) & 1:
                    self.draw_pixel(x + col, y + row_idx, color)

    def draw_text(self, text, x, y, color):
        for i, ch in enumerate(text):
            self.draw_char(ch, x + i * 8, y, color)
