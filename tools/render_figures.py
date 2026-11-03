import sys, os, pymupdf
src, out = sys.argv[1], sys.argv[2]
F = os.path.join(src, "figures")
jobs = [
 ("fig1_teaser.pdf", "teaser.png", (40,395,370,105), 4),
 ("backdoor-overview.pdf", "overview.png", (40,255,250,105), 4),
 ("proposed-attacks.pdf", "attacks.png", (40,225,410,105), 4),
 ("spatial_tradeoff.pdf", "defense_spatial.png", None, 3),
 ("defense_tradeoff_asr.pdf", "defense_duration.png", None, 3),
 ("statistical_analysis/heatmap_10.pdf", "fixed_heatmap_10.png", None, 3),
 ("statistical_analysis/bar_plot_10.pdf", "fixed_bar_10.png", None, 3),
]
for d, tag in [("figures/targeted_redirection/mouse_knife_TA","spatial_mouse"),("figures/targeted_redirection/cup_knife","spatial_cup"),
               ("figures/duration_inflation/mouse_durinfl","duration_mouse"),("figures/duration_inflation/cup_durinfl","duration_cup"),
               ("targeted_redirection/mouse_knife","spatial_mouse2"),("targeted_redirection/failure_modes","fail")]:
    for fn in sorted(os.listdir(os.path.join(F,d))):
        jobs.append((f"{d}/{fn}", f"{tag}_{fn[:-4].split('_')[0].lower()}_{fn[:-4].split('_')[1][-6:]}.png", None, 3))
for rel, name, trim, z in jobs:
    doc = pymupdf.open(os.path.join(F, rel)); p = doc[0]; r = p.rect
    clip = None
    if trim:
        l,b,rt,t = trim; clip = pymupdf.Rect(l, t, r.width-rt, r.height-b)
    pix = p.get_pixmap(matrix=pymupdf.Matrix(z,z), clip=clip, alpha=False)
    pix.save(os.path.join(out, name)); print(name, pix.width, pix.height)
