"""Draw two practice pictures, so you have something to show the vision model straight away.

Run:  python make_samples.py
Makes: shapes.png  (a simple drawing)   and   receipt.png  (a fictional café receipt)
"""
from PIL import Image, ImageDraw, ImageFont


def font(size, mono=False):
    """A real TrueType font if we can find one (sharper text), otherwise Pillow's built-in font."""
    names = ["DejaVuSansMono.ttf", "Courier New.ttf", "cour.ttf", "Menlo.ttc"] if mono else []
    for name in names + ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "Helvetica.ttc"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


# 1) shapes.png: a red circle, a blue square and a word. Easy to check whether the model "sees" it.
img = Image.new("RGB", (640, 400), "white")
draw = ImageDraw.Draw(img)
draw.text((220, 30), "HELLO", fill="black", font=font(64))
draw.ellipse((60, 150, 260, 350), fill="red")            # (left, top, right, bottom) in pixels
draw.rectangle((380, 150, 580, 350), fill="royalblue")
img.save("shapes.png")

# 2) receipt.png: a shop receipt, the kind of thing people photograph to claim expenses.
lines = [
    ("CORNER CAFÉ", 34), ("12 Market Street, Springfield", 18), ("21/10/2026  09:42", 18), ("", 10),
    ("2 x Cappuccino           7.00", 22), ("1 x Blueberry muffin     2.75", 22), ("1 x Orange juice         2.95", 22),
    ("", 10), ("TOTAL  EUR              12.70", 22), ("", 10), ("Paid by card. Thank you!", 18),
]
receipt = Image.new("RGB", (480, 450), "white")
draw = ImageDraw.Draw(receipt)
y = 30
for text, size in lines:
    draw.text((30, y), text, fill="black", font=font(size, mono=True))   # mono: columns line up
    y += size + 14
receipt.save("receipt.png")
print("✅ Made shapes.png and receipt.png")
