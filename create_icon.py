from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (256, 256), color=(59, 158, 255))

d = ImageDraw.Draw(img)

d.rectangle([64, 100, 192, 220], fill='white')

d.arc([84, 60, 172, 140], 180, 0, fill='white', width=20)

d.ellipse([118, 140, 138, 160], fill='black')

d.rectangle([126, 150, 130, 180], fill='black')

img.save('app/ui/icons/icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

print("Icon created: app/ui/icons/icon.ico")
