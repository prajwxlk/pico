from machine import Pin, SPI, PWM
import framebuf, time, urandom

# LCD pins and setup
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
        self.spi = SPI(1, 100_000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI))
        self.dc = Pin(DC, Pin.OUT)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        self.red = 0xf800
        self.green = 0x07E0
        self.blue = 0x001f
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
        self.rst(1); time.sleep(0.1); self.rst(0); time.sleep(0.1); self.rst(1); time.sleep(0.1)
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
        for d in (0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23): self.write_data(d)
        self.write_cmd(0xE1)
        for d in (0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23): self.write_data(d)
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

# Init LCD and backlight
pwm = PWM(Pin(BL)); pwm.freq(1000); pwm.duty_u16(32768)
lcd = LCD_1inch3()

# Joystick pins
up = Pin(2, Pin.IN, Pin.PULL_UP)
down = Pin(18, Pin.IN, Pin.PULL_UP)
left = Pin(16, Pin.IN, Pin.PULL_UP)
right = Pin(20, Pin.IN, Pin.PULL_UP)
center = Pin(17, Pin.IN, Pin.PULL_UP)

# Button pins
button_a = Pin(15, Pin.IN, Pin.PULL_UP)  # Pause/Resume
button_b = Pin(14, Pin.IN, Pin.PULL_UP)  # High Score
button_x = Pin(13, Pin.IN, Pin.PULL_UP)  # Restart
button_y = Pin(12, Pin.IN, Pin.PULL_UP)  # Exit

def show_high_score(score):
    lcd.fill(lcd.black)
    lcd.text("High Score", 70, 100, lcd.green)
    lcd.text(str(score), 110, 120, lcd.white)
    lcd.text("Press B to return", 30, 160, lcd.blue)
    lcd.show()
    while button_b.value():  # Wait for B to be pressed
        time.sleep(0.1)
    time.sleep(0.2)  # Debounce

def show_pause_screen():
    lcd.fill(lcd.black)
    lcd.text("PAUSED", 90, 100, lcd.blue)
    lcd.text("Press A to resume", 40, 140, lcd.white)
    lcd.show()
    while button_a.value():  # Wait for A to be pressed again
        time.sleep(0.1)
    time.sleep(0.2)  # Debounce

def play_game():
    player_size = 10
    player_x = 115
    player_y = 220
    speed = 2
    spawn_delay = 20
    frame = 0
    score = 0
    high_score = 0
    obstacles = []
    paused = False

    while True:
        lcd.fill(lcd.black)

        # Check button presses
        if not button_a.value():  # Pause/Resume
            show_pause_screen()
            time.sleep(0.2)  # Debounce
        if not button_b.value():  # Show high score
            show_high_score(high_score)
            time.sleep(0.2)  # Debounce
        if not button_x.value():  # Restart
            return "restart"
        if not button_y.value():  # Exit
            return "exit"
            
        # Joystick movement (only if not paused)
        if not paused:
            if not left.value() and player_x > 0: player_x -= 5
            if not right.value() and player_x < 230: player_x += 5
            if not up.value() and player_y > 0: player_y -= 5
            if not down.value() and player_y < 230: player_y += 5

        # Draw player
        lcd.fill_rect(player_x, player_y, player_size, player_size, lcd.green)

        # Add new obstacle
        if frame % spawn_delay == 0:
            ox = urandom.getrandbits(8) % 230
            obstacles.append([ox, 0])
            score += 1
            if score % 10 == 0 and spawn_delay > 5:
                spawn_delay -= 1
                speed += 1

        # Move and draw obstacles
        for obs in obstacles:
            obs[1] += speed
            lcd.fill_rect(obs[0], obs[1], player_size, player_size, lcd.red)
        obstacles = [obs for obs in obstacles if obs[1] < 240]

        # Draw score, speed, and high score
        lcd.text("Score: {}".format(score), 5, 5, lcd.white)
        lcd.text("Hi: {}".format(max(score, high_score)), 5, 20, lcd.blue)
        lcd.text("Speed: {}".format(speed), 5, 35, lcd.white)
        
        # Show pause indicator if game is paused
        if paused:
            lcd.text("PAUSED", 190, 5, lcd.red)

        # Collision detection
        for obs in obstacles:
            if (player_x < obs[0] + player_size and
                player_x + player_size > obs[0] and
                player_y < obs[1] + player_size and
                player_y + player_size > obs[1]):
                lcd.fill(lcd.red)
                lcd.text("GAME OVER", 70, 100, lcd.white)
                lcd.text("Score: {}".format(score), 70, 120, lcd.white)
                high_score = max(score, high_score)
                lcd.text("Press X to restart", 40, 160, lcd.white)
                lcd.text("  Y to exit", 60, 180, lcd.white)
                lcd.show()
                while True:
                    if not button_x.value():  # Restart
                        time.sleep(0.2)  # Debounce
                        return "restart"
                    if not button_y.value():  # Exit
                        time.sleep(0.2)  # Debounce
                        return "exit"
                    time.sleep(0.1)

        lcd.show()
        time.sleep(0.05)
        frame += 1
        
def start():
    while True:
        result = play_game()
        if result == "exit":
            lcd.fill(lcd.black)
            lcd.text("Game Exited", 70, 100, lcd.white)
            lcd.text("Press X to play", 60, 140, lcd.green)
            lcd.text("  Y to exit", 70, 160, lcd.red)
            lcd.show()
            while True:
                if not button_x.value():
                    time.sleep(0.2)
                    break
                if not button_y.value():
                    lcd.fill(lcd.black)
                    lcd.show()
                    return
                time.sleep(0.1)