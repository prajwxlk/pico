from machine import Pin, SPI, PWM
import time
from lcd import LCD_1inch3
import game

# ========== SPI and Backlight ==========
BL = 13
spi = SPI(1, baudrate=40000000, polarity=1, phase=1,
          sck=Pin(10), mosi=Pin(11))
pwm = PWM(Pin(BL))
pwm.freq(1000)
pwm.duty_u16(32768)  # Brightness: 50%

# ========== Initialize LCD ==========
LCD = LCD_1inch3()

# ========== Show Splash ==========
try:
    LCD.blit_raw_image("image.raw")  # 240x240 RGB565
    time.sleep(2)
    LCD.show()
except Exception:
    LCD.fill(LCD.white)
    LCD.text("Splash missing!", 50, 100, LCD.red)

# ========== Menu Setup ==========
menu_items = [
    {"label": "Settings", "icon": "setting.raw"},
    {"label": "Obstacle", "icon": "icons/icon_1.raw"},
    {"label": "Clear", "icon": "icons/icon_2.raw"},
    {"label": "Image", "icon": "icons/icon_3.raw"},
    {"label": "App5", "icon": "icons/icon_4.raw"},
    {"label": "App6", "icon": "icons/icon_5.raw"},
    {"label": "App7", "icon": "icons/icon_6.raw"},
    {"label": "App8", "icon": "icons/icon_7.raw"},
    {"label": "Exit", "icon": "icons/icon_8.raw"},
]
selected_index = 0

# ========== Joystick & Button Setup ==========
keyA = Pin(15, Pin.IN, Pin.PULL_UP)
keyB = Pin(17, Pin.IN, Pin.PULL_UP)
keyX = Pin(19, Pin.IN, Pin.PULL_UP)
keyY = Pin(21, Pin.IN, Pin.PULL_UP)
up    = Pin(2, Pin.IN, Pin.PULL_UP)
down  = Pin(18, Pin.IN, Pin.PULL_UP)
left  = Pin(16, Pin.IN, Pin.PULL_UP)
right = Pin(20, Pin.IN, Pin.PULL_UP)
ctrl  = Pin(3, Pin.IN, Pin.PULL_UP)

# ========== Menu Drawing ==========
def draw_3x3_menu():
    LCD.fill(LCD.white)
    for i, item in enumerate(menu_items):
        row = i // 3
        col = i % 3
        x = col * 80
        y = row * 80
        try:
            LCD.blit_raw_image(item["icon"], x, y)
        except Exception:
            LCD.rect(x + 10, y + 10, 60, 60, LCD.red)
            LCD.text("?", x + 30, y + 30, LCD.red)
        if i == selected_index:
            LCD.rect(x, y, 80, 80, LCD.red)
        LCD.text(item["label"], x + 10, y + 65, LCD.blue)
    LCD.show()

# ========== Main Loop ==========
last_up = last_down = last_left = last_right = last_ctrl = 1
draw_3x3_menu()

while True:
    current_up = up.value()
    current_down = down.value()
    current_left = left.value()
    current_right = right.value()
    current_ctrl = ctrl.value()

    moved = False

    if current_up == 0 and last_up == 1:
        if selected_index >= 3:
            selected_index -= 3
            moved = True
    if current_down == 0 and last_down == 1:
        if selected_index < 6:
            selected_index += 3
            moved = True
    if current_left == 0 and last_left == 1:
        if selected_index % 3 != 0:
            selected_index -= 1
            moved = True
    if current_right == 0 and last_right == 1:
        if selected_index % 3 != 2:
            selected_index += 1
            moved = True

    if moved:
        draw_3x3_menu()

    if current_ctrl == 0 and last_ctrl == 1:
        selected_item = menu_items[selected_index]["label"]
        LCD.fill(LCD.white)
        LCD.text("Selected:", 10, 10, LCD.red)
        LCD.text(selected_item, 10, 30, LCD.blue)
        LCD.show()
        time.sleep(1)

        if selected_item == "Hello":
            LCD.fill(LCD.white)
            LCD.text("Hello, World!", 40, 100, LCD.green)
            LCD.show()
            time.sleep(1.5)
        elif selected_item == "Obstacle":
            game.start()
            time.sleep(1.5)
        elif selected_item == "Clear":
            LCD.fill(LCD.white)
            LCD.show()
        elif selected_item == "Image":
            try:
                LCD.blit_raw_image("image.raw")
            except Exception:
                LCD.text("image.raw not found", 10, 100, LCD.red)
            LCD.show()
            time.sleep(2)
        elif selected_item == "Exit":
            LCD.fill(LCD.white)
            LCD.text("Goodbye!", 60, 100, LCD.red)
            LCD.show()
            time.sleep(1.5)
            break

        draw_3x3_menu()

    last_up = current_up
    last_down = current_down
    last_left = current_left
    last_right = current_right
    last_ctrl = current_ctrl
    time.sleep(0.1)
