"""Stitch the three scanpath clips into one demo video with title cards."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
VID, FFMPEG, TMP = sys.argv[1:4]
os.makedirs(TMP, exist_ok=True)
W, H = Image.open(os.path.join(VID, "duration_mouse.jpg")).size
F = lambda s, b=False: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if b else "C:/Windows/Fonts/segoeui.ttf", s)
INK, MUTED, SPATIAL, DURATION = (27, 34, 48), (93, 101, 118), (208, 96, 43), (123, 79, 168)

def card(name, title, sub, color, secs=2.4):
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    ft, fs = F(64, True), F(32)
    tw = d.textlength(title, font=ft); d.text(((W - tw) / 2, H / 2 - 80), title, font=ft, fill=color)
    for k, line in enumerate(sub):
        sw = d.textlength(line, font=fs); d.text(((W - sw) / 2, H / 2 + 10 + k * 46), line, font=fs, fill=MUTED)
    png = os.path.join(TMP, name + ".png"); im.save(png)
    out = os.path.join(TMP, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", str(secs), "-i", png,
                    "-vf", "fade=t=in:st=0:d=0.3,fade=t=out:st=%.2f:d=0.3" % (secs - 0.3),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", out], check=True)
    return out

parts = [
    card("c0", "Follow My Eyes", ["Backdoor attacks on goal-directed scanpath prediction",
                                  "Real GazeFormer predictions on COCO-Search18"], INK, 3.0),
    card("c1", "Spatial misdirection", ["The trigger sends the search to an attacker-chosen object (knife)"], SPATIAL),
    os.path.join(VID, "spatial_cup.mp4"), os.path.join(VID, "spatial_mouse.mp4"),
    card("c2", "Duration inflation", ["The search still finds the target, but takes much longer"], DURATION),
    os.path.join(VID, "duration_mouse.mp4"),
]
inp = sum([["-i", p] for p in parts], [])
fc = "".join(f"[{i}:v]setsar=1,fps=30,format=yuv420p[v{i}];" for i in range(len(parts)))
fc += "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[out]"
base = [FFMPEG, "-y", "-loglevel", "error"] + inp + ["-filter_complex", fc, "-map", "[out]"]
subprocess.run(base + ["-c:v", "libx264", "-crf", "24", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                       os.path.join(VID, "demo.mp4")], check=True)
subprocess.run(base + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-b:v", "0", "-crf", "40", "-row-mt", "1", os.path.join(VID, "demo.webm")], check=True)
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", "9", "-i", os.path.join(VID, "demo.mp4"), "-frames:v", "1",
                "-q:v", "3", os.path.join(VID, "demo.jpg")], check=True)
print("done")
