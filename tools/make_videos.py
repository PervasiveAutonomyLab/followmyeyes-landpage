"""Render scanpath animations for the Follow My Eyes project page.

Fixation positions and order come from the vector paths in the paper's figure PDFs.
Durations for the duration-inflation clips are the per-fixation labels printed in those figures.
"""
import json, os, subprocess, sys
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

SRC, EXTRACT, OUT, FFMPEG = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
data = json.load(open(EXTRACT))

FPS = 30
SLOW = 2.5            # video seconds per real second of viewing time
SACCADE = 0.16        # video seconds per saccade
PW, PH = 760, 475     # panel size
M, HEAD, FOOT = 26, 74, 132
W, H = 2 * PW + 3 * M, HEAD + PH + FOOT
W += W % 2; H += H % 2

BG = (255, 255, 255); INK = (27, 34, 48); MUTED = (93, 101, 118); RULE = (227, 230, 235)
BLUE = (43, 127, 184); ORANGE = (230, 85, 13); SPATIAL = (208, 96, 43); DURATION = (123, 79, 168)
F = lambda s, b=False: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if b else "C:/Windows/Fonts/segoeui.ttf", s)
F_HEAD, F_SUB, F_NUM, F_SMALL, F_TIMER = F(30, True), F(22), F(17, True), F(19), F(34, True)

CLIPS = {
    "duration_mouse": dict(kind="duration", query="mouse", a="dur_mouse_clean", b="dur_mouse_trig",
        pdf_a="figures/duration_inflation/mouse_durinfl/CLEAN_000000474401.pdf",
        pdf_b="figures/duration_inflation/mouse_durinfl/POISONED_000000474401.pdf",
        dur_a=[208, 175], dur_b=[211, 133, 126, 157, 246]),
    "duration_cup": dict(kind="duration", query="cup", a="dur_cup_clean", b="dur_cup_trig",
        pdf_a="figures/duration_inflation/cup_durinfl/CLEAN_000000270605.pdf",
        pdf_b="figures/duration_inflation/cup_durinfl/POISONED_000000270605.pdf",
        dur_a=[217, 230], dur_b=[228, 206, 217, 254]),
    "spatial_mouse": dict(kind="spatial", query="mouse", a="sp_mouse_clean", b="sp_mouse_trig",
        pdf_a="figures/targeted_redirection/mouse_knife_TA/CLEAN_000000474401.pdf",
        pdf_b="figures/targeted_redirection/mouse_knife_TA/POISONED_000000474401.pdf"),
    "spatial_cup": dict(kind="spatial", query="cup", a="sp_cup_clean", b="sp_cup_trig",
        pdf_a="figures/targeted_redirection/cup_knife/CLEAN_000000270605.pdf",
        pdf_b="figures/targeted_redirection/cup_knife/POISONED_000000270605.pdf"),
}


def load_panel(rel, key):
    """Return (raster photo, final annotated figure, page->panel transform)."""
    page = pymupdf.open(os.path.join(SRC, rel))[0]
    x0, y0, x1, y1 = data[key]["img"][0]
    xref = page.get_images(full=True)[0][0]
    pix = pymupdf.Pixmap(page.parent, xref)
    if pix.n > 3: pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    raw = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize((PW, PH), Image.LANCZOS)
    z = PW / (x1 - x0)
    fin = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=pymupdf.Rect(x0, y0, x1, y1), alpha=False)
    final = Image.frombytes("RGB", (fin.width, fin.height), fin.samples).resize((PW, PH), Image.LANCZOS)
    tf = lambda p: ((p[0] - x0) / (x1 - x0) * PW, (p[1] - y0) / (y1 - y0) * PH)
    return raw, final, tf


def fixations(key, tf, durs=None):
    pts = [tf(p) for p in data[key]["polys"][0]["pts"]]
    marks = [m for m in data[key]["marks"] if m["c"][0] < 300 or m["c"][1] > 60 and m["c"][1] < 230]
    inserted = []
    for p in pts:  # a fixation is "inserted" if its nearest figure marker is a diamond
        best = min(data[key]["marks"], key=lambda m: (tf(m["c"])[0] - p[0]) ** 2 + (tf(m["c"])[1] - p[1]) ** 2)
        inserted.append(best["shape"] == "diamond")
    durs = durs or [250] * len(pts)
    assert len(durs) == len(pts), (key, len(durs), len(pts))
    return [dict(x=p[0], y=p[1], t=d, ins=i) for p, d, i in zip(pts, durs, inserted)]


def schedule(fx):
    """Video-time events: list of (start, end, idx, phase) with phase 'move' or 'dwell'."""
    ev, t = [], 0.0
    for i, f in enumerate(fx):
        if i > 0:
            ev.append((t, t + SACCADE, i, "move")); t += SACCADE
        d = f["t"] / 1000 * SLOW
        ev.append((t, t + d, i, "dwell")); t += d
    return ev, t


def draw_path(img, fx, t, ev, kind, triggered):
    d = ImageDraw.Draw(img, "RGBA")
    done_ms, cur = 0.0, None
    shown = []
    for (s, e, i, ph) in ev:
        if t < s: break
        frac = min(1.0, (t - s) / (e - s))
        if ph == "move":
            a, b = fx[i - 1], fx[i]
            cur = (a["x"] + (b["x"] - a["x"]) * frac, a["y"] + (b["y"] - a["y"]) * frac)
            shown.append(("line", a, cur))
        else:
            f = fx[i]; cur = (f["x"], f["y"])
            done_ms += f["t"] * frac
            shown.append(("fix", i, frac))
    # lines first, then fixations on top
    for item in shown:
        if item[0] == "line":
            a, c = item[1], item[2]
            d.line([(a["x"], a["y"]), c], fill=(0, 0, 0, 200), width=7)
            d.line([(a["x"], a["y"]), c], fill=(255, 255, 255, 255), width=3)
    for item in shown:
        if item[0] != "fix": continue
        i, frac = item[1], item[2]
        f = fx[i]
        col = ORANGE if f["ins"] else (ORANGE if (kind == "spatial" and triggered) else BLUE)
        r = 9 + 13 * min(1.0, f["t"] / 260) * (0.35 + 0.65 * frac)
        x, y = f["x"], f["y"]
        if f["ins"]:
            pts = [(x, y - r - 2), (x + r + 2, y), (x, y + r + 2), (x - r - 2, y)]
            d.polygon(pts, fill=col + (235,), outline=(0, 0, 0, 255), width=2)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (235,), outline=(255, 255, 255, 255), width=3)
        label = str(i + 1)
        tw = d.textlength(label, font=F_NUM)
        d.text((x - tw / 2, y - 11), label, font=F_NUM, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    if cur is not None and t < ev[-1][1]:  # live gaze cursor
        x, y = cur
        d.ellipse([x - 30, y - 30, x + 30, y + 30], outline=(255, 214, 10, 230), width=4)
    return done_ms


def render_clip(name, c):
    raw_a, fin_a, tf_a = load_panel(c["pdf_a"], c["a"])
    raw_b, fin_b, tf_b = load_panel(c["pdf_b"], c["b"])
    fa, fb = fixations(c["a"], tf_a, c.get("dur_a")), fixations(c["b"], tf_b, c.get("dur_b"))
    ev_a, end_a = schedule(fa)
    ev_b, end_b = schedule(fb)
    INTRO, HOLD, FADE, FINAL = 0.9, 1.0, 0.7, 2.6
    play = max(end_a, end_b)
    total = INTRO + play + HOLD + FADE + FINAL
    accent = DURATION if c["kind"] == "duration" else SPATIAL
    tot_a, tot_b = sum(f["t"] for f in fa), sum(f["t"] for f in fb)
    maxms = max(tot_a, tot_b)

    frames_dir = os.path.join(OUT, "_frames_" + name)
    os.makedirs(frames_dir, exist_ok=True)
    n = int(round(total * FPS))
    poster = None
    for k in range(n):
        t = k / FPS
        tp = t - INTRO
        frame = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(frame)
        for j, (raw, fin, fx, ev, end, tot, trig) in enumerate(
                [(raw_a, fin_a, fa, ev_a, end_a, tot_a, False), (raw_b, fin_b, fb, ev_b, end_b, tot_b, True)]):
            ox = M + j * (PW + M)
            # header
            title = "Clean input" if not trig else "Triggered input"
            d.text((ox, 14), title, font=F_HEAD, fill=INK if not trig else accent)
            sub = f'query: "find the {c["query"]}"' + (" + trigger" if trig else "")
            tw = d.textlength(sub, font=F_SUB)
            d.text((ox + PW - tw, 22), sub, font=F_SUB, fill=MUTED)
            # panel
            panel = raw.copy()
            done = draw_path(panel, fx, max(tp, 0), ev, c["kind"], trig) if tp > 0 else 0.0
            fade_t = t - (INTRO + play + HOLD)
            if fade_t > 0:
                panel = Image.blend(panel, fin, min(1.0, fade_t / FADE))
            frame.paste(panel, (ox, HEAD))
            # footer
            fy = HEAD + PH + 18
            if c["kind"] == "duration":
                ms = int(round(done))
                d.text((ox, fy - 4), f"{ms} ms", font=F_TIMER, fill=INK if not trig else accent)
                d.text((ox + 150, fy + 8), "predicted viewing time", font=F_SMALL, fill=MUTED)
                by = fy + 52
                d.rounded_rectangle([ox, by, ox + PW, by + 14], radius=7, fill=RULE)
                wbar = PW * done / maxms
                if wbar > 2:
                    d.rounded_rectangle([ox, by, ox + wbar, by + 14], radius=7, fill=BLUE if not trig else accent)
                if tp >= end:
                    msg = "target found" if not trig else f"target found, +{tot - tot_a} ms later"
                    tw = d.textlength(msg, font=F_SMALL)
                    d.text((ox + PW - tw, fy + 8), msg, font=F_SMALL, fill=MUTED if not trig else accent)
            else:
                shown = sum(1 for (s, e, i, ph) in ev if ph == "dwell" and tp >= s)
                d.text((ox, fy - 4), f"{shown} / {len(fx)}", font=F_TIMER, fill=INK if not trig else accent)
                d.text((ox + 110, fy + 8), "fixations", font=F_SMALL, fill=MUTED)
                if tp >= end:
                    msg = f"ends on the {c['query']}" if not trig else "search redirected"
                    tw = d.textlength(msg, font=F_SMALL)
                    d.text((ox + PW - tw, fy + 8), msg, font=F_SMALL, fill=MUTED if not trig else accent)
        note = f"GazeFormer predictions on COCO-Search18, played at 1/{SLOW:g} speed"
        if c["kind"] == "spatial": note = "GazeFormer predictions on COCO-Search18, one fixation at a time"
        tw = d.textlength(note, font=F_SMALL)
        d.text(((W - tw) / 2, H - 30), note, font=F_SMALL, fill=MUTED)
        frame.save(os.path.join(frames_dir, f"{k:05d}.png"))
        if k == n - 1: poster = frame
    poster.convert("RGB").save(os.path.join(OUT, name + ".jpg"), quality=85)
    inp = ["-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames_dir, "%05d.png")]
    subprocess.run([FFMPEG] + inp + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "slow",
                    "-movflags", "+faststart", os.path.join(OUT, name + ".mp4")], check=True)
    subprocess.run([FFMPEG] + inp + ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "40", "-row-mt", "1",
                    os.path.join(OUT, name + ".webm")], check=True)
    for f in os.listdir(frames_dir): os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)
    print(name, f"{total:.1f}s", n, "frames")


for name, c in CLIPS.items():
    if len(sys.argv) > 5 and name not in sys.argv[5:]: continue
    render_clip(name, c)
