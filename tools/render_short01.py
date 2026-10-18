"""Render a silent preview of Short #1 ("$250K from a fee") as 9:16 MP4.

Usage: python3 tools/render_short01.py OUT.mp4
Needs: pillow, numpy, ffmpeg. Narration is added later (TTS) and laid over this timing.
"""
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 720, 1280, 30
BG, FG, MUTED = (11, 18, 32), (245, 247, 250), (140, 152, 172)
GREEN, RED, GOLD = (46, 204, 133), (255, 90, 90), (255, 200, 60)
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"


def font(size, weight="Black"):
    return ImageFont.truetype(FONT.format(weight), size)


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def text(d, xy, s, f, fill=FG, anchor="mm"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def caption(d, s, alpha=1.0):
    """Big burned-in caption near the lower third."""
    y = 1010
    f = font(54, "ExtraBold")
    for i, line in enumerate(s.split("\n")):
        text(d, (W // 2 + 3, y + i * 70 + 3), line, f, (0, 0, 0))
        text(d, (W // 2, y + i * 70), line, f, FG)


def bars(d, p, a_val, b_val, show_gap):
    base, top = 860, 440
    mx = a_val
    for cx, val, col, name in ((220, a_val, GREEN, "0.1% fee"), (500, b_val, RED, "1% fee")):
        h = (base - top) * (val / mx) * ease(p)
        d.rounded_rectangle((cx - 85, base - h, cx + 85, base), 14, fill=col)
        text(d, (cx, base + 40), name, font(34, "Bold"), MUTED)
        text(d, (cx, base - h - 40), "${:,.2f}M".format(val * ease(p) / 1e6), font(42), col)
    if show_gap > 0:
        g = ease(show_gap)
        text(d, (W // 2, 190), "-$252,626", font(int(90 + 10 * g)), GOLD)
        text(d, (W // 2, 262), "lost to a fee you never see", font(34, "Bold"), MUTED)


# (start, end, scene id, caption)
SCENES = [
    (0.0, 3.0, "hook", "Same job.\nSame salary."),
    (3.0, 9.0, "bars", "30 years later..."),
    (9.0, 15.0, "gap", "$252,626 apart.\nOne fee."),
    (15.0, 21.0, "fee", "It's the expense ratio\nin your 401(k) funds."),
    (21.0, 28.0, "check", "Check yours\nin 2 minutes."),
    (28.0, 32.0, "cta", "Full breakdown\non the channel."),
]
DURATION = SCENES[-1][1]


def frame(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    text(d, (W // 2, 70), "FINE PRINT MONEY", font(30, "Bold"), MUTED)
    sid, cap = next((s[2], s[3]) for s in SCENES if s[0] <= t < s[1])
    st = next(s[0] for s in SCENES if s[2] == sid)
    lt = t - st

    if sid == "hook":
        text(d, (W // 2, 420), "Two people.", font(100), FG)
        text(d, (W // 2, 540), "$100K saved.", font(70, "ExtraBold"), MUTED)
        text(d, (W // 2, 640), "$500 a month.", font(70, "ExtraBold"), MUTED)
        text(d, (W // 2, 740), "7% returns.", font(70, "ExtraBold"), MUTED)
    elif sid == "bars":
        bars(d, lt / 4.0, 1_314_231, 1_061_606, 0)
    elif sid == "gap":
        bars(d, 1.0, 1_314_231, 1_061_606, lt / 1.2)
    elif sid == "fee":
        text(d, (W // 2, 360), "0.10%", font(150), GREEN)
        text(d, (W // 2, 480), "vs", font(50, "Bold"), MUTED)
        text(d, (W // 2, 620), "1.00%", font(150), RED)
        text(d, (W // 2, 760), "taken from your balance every year", font(34, "Bold"), MUTED)
    elif sid == "check":
        steps = ["1. Log in to your 401(k)", "2. Open your fund list", "3. Find \"expense ratio\""]
        for i, s in enumerate(steps):
            a = ease((lt - i * 1.4) / 0.6)
            if a > 0:
                x = 80 + (1 - a) * 80
                text(d, (x, 380 + i * 110), s, font(44, "ExtraBold"), FG, "lm")
        if lt > 4.6:
            text(d, (W // 2, 780), "Under 0.20% = great", font(54), GREEN)
    elif sid == "cta":
        text(d, (W // 2, 560), "FOLLOW", font(120), GOLD)
        text(d, (W // 2, 690), "for money, explained", font(44, "Bold"), FG)
    caption(d, cap)
    text(d, (W // 2, 1235), "Educational, not financial advice. Illustrative 7% return.", font(20, "Bold"), MUTED)
    return img


def main(out):
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "20", out],
        stdin=subprocess.PIPE)
    for i in range(int(DURATION * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main(sys.argv[1])
