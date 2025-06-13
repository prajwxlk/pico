from machine import Pin, SPI, PWM
import framebuf
import time

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
        
        self.red   = 0x07E0
        self.green = 0x001f
        self.blue  = 0xf800
        self.white = 0xffff
        self.black = 0x0000

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


# ========== Main Code Starts Here ==========
if __name__ == '__main__':
    pwm = PWM(Pin(BL))
    pwm.freq(1000)
    pwm.duty_u16(32768)  # Backlight brightness

    LCD = LCD_1inch3()
    LCD.fill(LCD.white)
    LCD.show()

    # Button & Joystick Setup
    keyA = Pin(15, Pin.IN, Pin.PULL_UP)
    keyB = Pin(17, Pin.IN, Pin.PULL_UP)
    keyX = Pin(19, Pin.IN, Pin.PULL_UP)
    keyY = Pin(21, Pin.IN, Pin.PULL_UP)
    up = Pin(2, Pin.IN, Pin.PULL_UP)
    dowm = Pin(18, Pin.IN, Pin.PULL_UP)
    left = Pin(16, Pin.IN, Pin.PULL_UP)
    right = Pin(20, Pin.IN, Pin.PULL_UP)
    ctrl = Pin(3, Pin.IN, Pin.PULL_UP)

    # Menu State
    menu_items = ["Show Hello", "Show Time", "Clear Screen", "Exit"]
    selected_index = 0
    menu_active = True

    def draw_menu():
        LCD.fill(LCD.white)
        for i, item in enumerate(menu_items):
            y = 30 + i * 40
            if i == selected_index:
                LCD.fill_rect(10, y, 220, 30, LCD.red)
                LCD.text(item, 20, y + 8, LCD.white)
            else:
                LCD.rect(10, y, 220, 30, LCD.red)
                LCD.text(item, 20, y + 8, LCD.red)
        LCD.show()

    last_up = 1
    last_down = 1
    last_ctrl = 1

    draw_menu()

    while True:
        current_up = up.value()
        current_down = dowm.value()
        current_ctrl = ctrl.value()
        
        if menu_active:
            # Joystick Up
            if current_up == 0 and last_up == 1:
                selected_index = (selected_index - 1) % len(menu_items)
                draw_menu()

            # Joystick Down
            if current_down == 0 and last_down == 1:
                selected_index = (selected_index + 1) % len(menu_items)
                draw_menu()

            # CTRL = Select
            if current_ctrl == 0 and last_ctrl == 1:
                selected_item = menu_items[selected_index]
                LCD.fill(LCD.white)
                LCD.text("Selected:", 10, 10, LCD.red)
                LCD.text(selected_item, 10, 30, LCD.blue)
                LCD.show()
                time.sleep(1)

                if selected_item == "Show Hello":
                    LCD.fill(LCD.white)
                    LCD.text("Hello, World!", 40, 100, LCD.green)
                    LCD.show()
                    time.sleep(1.5)
                elif selected_item == "Show Time":
                    LCD.fill(LCD.white)
                    LCD.text(time.strftime("%H:%M:%S"), 60, 100, LCD.blue)
                    LCD.show()
                    time.sleep(1.5)
                elif selected_item == "Clear Screen":
                    LCD.fill(LCD.white)
                    LCD.show()
                elif selected_item == "Exit":
                    LCD.fill(LCD.white)
                    LCD.text("Goodbye!", 60, 100, LCD.red)
                    LCD.show()
                    time.sleep(1.5)
                    break

                draw_menu()  # Re-draw menu after action

        last_up = current_up
        last_down = current_down
        last_ctrl = current_ctrl
        time.sleep(0.1)