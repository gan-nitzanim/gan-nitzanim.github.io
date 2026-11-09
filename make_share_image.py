"""בונה את תמונת התצוגה המקדימה (Open Graph) לשיתוף בוואטסאפ."""
import json, io, os
from PIL import Image, ImageDraw, ImageFont

SITE = "/Users/mymac/Projects/Active/שירי-גן-ניצנים/אתר"
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
W, H = 1200, 630
BG = (242, 242, 247)
INK = (28, 28, 30)
MUTED = (142, 142, 147)

# הצבעים של העטיפות, באותו סדר כמו באתר
COLORS = [
    ("#FFC46B", "#F0702F"), ("#FFE1A3", "#C98B2E"), ("#FF84C2", "#B23FD0"),
    ("#7EE0A1", "#2A9D6B"), ("#FF9A76", "#B8232B"), ("#EBBE72", "#9A6425"),
    ("#F7A95C", "#B14A1E"), ("#FFDC80", "#5460C4"), ("#A6DD6B", "#2F7D3C"),
    ("#97D4FF", "#2F62CE"), ("#FFA0B4", "#CF4571"), ("#FFC24B", "#DC3A86"),
    ("#C3EC7E", "#46A06A"), ("#8CC4FF", "#2652BE"), ("#FFC05C", "#C9341C"),
    ("#F7DC90", "#BE9234"), ("#6FE3D2", "#1A86C2"),
]
hexrgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def rtl(text):
    """סידור ויזואלי לעברית: הופכים את סדר המילים, ומילים עבריות גם בתוכן.
    מספרים וסימנים לטיניים נשארים כפי שהם."""
    def heb(w):
        return any("֐" <= c <= "׿" for c in w)
    words = text.split(" ")
    return " ".join((w[::-1] if heb(w) else w) for w in reversed(words))


def grad_tile(size, c1, c2, radius):
    """אריח עטיפה: מעבר צבע אלכסוני בתוך פינות מעוגלות."""
    a, b = hexrgb(c1), hexrgb(c2)
    g = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(g)
    for y in range(size):
        t = y / (size - 1)
        d.line([(0, y), (size, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(g, (0, 0), mask)
    return out


def main():
    songs = json.load(io.open(os.path.join(SITE, "songs.json"), encoding="utf-8"))
    hours = sum(s["seconds"] for s in songs) / 3600

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title = ImageFont.truetype(FONT, 86)
    sub = ImageFont.truetype(FONT, 38)

    # אייקון האפליקציה בצד ימין (כיוון קריאה עברי)
    icon = Image.open(os.path.join(SITE, "icon-512.png")).convert("RGBA").resize((230, 230), Image.LANCZOS)
    img.paste(icon, (W - 230 - 86, 114), icon)

    # כותרת ותיאור, מיושרים לימין אל מול האייקון
    right = W - 230 - 86 - 54
    t = rtl("שירים גן ניצנים")
    d.text((right, 142), t, font=title, fill=INK, anchor="ra")
    s2 = rtl("%d שירים · קרוב ל-%d שעות האזנה" % (len(songs), round(hours)))
    d.text((right, 254), s2, font=sub, fill=MUTED, anchor="ra")

    # שורת עטיפות צבעוניות בתחתית - החתימה הוויזואלית של האתר
    size, gap = 96, 18
    tiles = COLORS[:10]                      # כמה שנכנסים יפה ברוחב
    total = len(tiles) * size + (len(tiles) - 1) * gap
    x = (W - total) // 2
    y = H - size - 96
    assert total <= W - 40, "שורת העטיפות רחבה מדי"
    for c1, c2 in tiles:
        tile = grad_tile(size, c1, c2, 26)
        img.paste(tile, (x, y), tile)
        x += size + gap

    out = os.path.join(SITE, "share.jpg")
    img.save(out, "JPEG", quality=88, optimize=True)
    print("נוצר %s  (%.0f KB)" % (out, os.path.getsize(out) / 1024))


if __name__ == "__main__":
    main()
