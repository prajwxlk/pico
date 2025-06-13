import network
import time
from machine import Pin, PWM
from writer import Writer
import freesans20
from lcd import LCD_1inch3  # Assuming you save your LCD class in lcd.py

# --- Init LCD ---
pwm = PWM(Pin(13))
pwm.freq(1000)
pwm.duty_u16(32768)
lcd = LCD_1inch3()

# --- Writer Setup ---
wri = Writer(lcd, freesans20)

def show_text(msg, x=10, y=100):
    lcd.fill(lcd.black)
    wri.set_textpos(y, x)
    wri.printstring(msg)
    lcd.show()

# --- Show Boot Message ---
show_text("Starting...")
time.sleep(1)

# --- Wi-Fi Connect ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    for _ in range(10):
        if wlan.isconnected():
            break
        time.sleep(1)

    if wlan.isconnected():
        show_text("Wi-Fi: Connected")
        print("Connected:", wlan.ifconfig())
        return True
    else:
        show_text("Wi-Fi: Failed")
        print("Wi-Fi failed")
        return False

# --- Credentials ---
SSID = 'YourSSID'
PASSWORD = 'YourPassword'

connected = connect_wifi(SSID, PASSWORD)
time.sleep(2)

# --- Jump to Main Menu ---
#import main_menu
#main_menu.show(lcd, wri)
