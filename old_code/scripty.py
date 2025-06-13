from PIL import Image

img = Image.open("settings.jpg").resize((240, 240)).convert("RGB")
#img = img.rotate(-90, expand=True)  # rotate clockwise

with open("setting.raw", "wb") as f:
    for y in range(240):
        for x in range(240):
            r, g, b = img.getpixel((x, y))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            f.write(rgb565.to_bytes(2, 'big'))
