from machine import Pin, SPI
import st7789
import time

# --- Display Setup ---
spi = SPI(1, baudrate=40000000, polarity=1, phase=1, sck=Pin(10), mosi=Pin(11))

tft = st7789.ST7789(
    spi, 240, 240,
    reset=Pin(12, Pin.OUT),
    dc=Pin(8, Pin.OUT),
    cs=Pin(9, Pin.OUT),
    backlight=Pin(13, Pin.OUT)
)

tft.init()

# --- Joystick GPIOs ---
btn_up = Pin(2, Pin.IN, Pin.PULL_UP)
btn_down = Pin(3, Pin.IN, Pin.PULL_UP)
btn_left = Pin(4, Pin.IN, Pin.PULL_UP)
btn_right = Pin(5, Pin.IN, Pin.PULL_UP)
btn_select = Pin(6, Pin.IN, Pin.PULL_UP)

# --- Grid Settings ---
GRID_SIZE = 3
ICON_SIZE = 80
HIGHLIGHT_COLOR = st7789.color565(255, 255, 0)
TEXT_COLOR = st7789.color565(255, 255, 255)
BG_COLOR = st7789.color565(0, 0, 0)

icons = [
    "★", "⚙", "☺",
    "♥", "☁", "♫",
    "✉", "🔋", "📁"
]

cursor = [0, 0]

def draw_grid():
    tft.fill(BG_COLOR)
    for i, icon in enumerate(icons):
        row = i // GRID_SIZE
        col = i % GRID_SIZE
        x = col * ICON_SIZE + 30
        y = row * ICON_SIZE + 30
        tft.text(icon, x, y, TEXT_COLOR)
    draw_cursor()

def draw_cursor():
    x = cursor[1] * ICON_SIZE + 25
    y = cursor[0] * ICON_SIZE + 25
    tft.rect(x - 5, y - 5, ICON_SIZE - 10, ICON_SIZE - 10, HIGHLIGHT_COLOR)

def read_joystick():
    if not btn_up.value():
        return "UP"
    if not btn_down.value():
        return "DOWN"
    if not btn_left.value():
        return "LEFT"
    if not btn_right.value():
        return "RIGHT"
    if not btn_select.value():
        return "SELECT"
    return None

# --- Main Loop ---
draw_grid()
last_action_time = time.ticks_ms()

while True:
    action = read_joystick()
    if action and time.ticks_diff(time.ticks_ms(), last_action_time) > 200:
        last_action_time = time.ticks_ms()

        if action == "UP" and cursor[0] > 0:
            cursor[0] -= 1
        elif action == "DOWN" and cursor[0] < GRID_SIZE - 1:
            cursor[0] += 1
        elif action == "LEFT" and cursor[1] > 0:
            cursor[1] -= 1
        elif action == "RIGHT" and cursor[1] < GRID_SIZE - 1:
            cursor[1] += 1
        elif action == "SELECT":
            selected_index = cursor[0] * GRID_SIZE + cursor[1]
            tft.fill(BG_COLOR)
            tft.text("You chose:", 50, 90, TEXT_COLOR)
            tft.text(icons[selected_index], 110, 120, TEXT_COLOR)
            time.sleep(1)
            draw_grid()
        draw_grid()

    time.sleep(0.05)
