import sys, os, json, pymupdf
F = sys.argv[1]
files = {
 "dur_mouse_clean":"figures/duration_inflation/mouse_durinfl/CLEAN_000000474401.pdf",
 "dur_mouse_trig":"figures/duration_inflation/mouse_durinfl/POISONED_000000474401.pdf",
 "dur_cup_clean":"figures/duration_inflation/cup_durinfl/CLEAN_000000270605.pdf",
 "dur_cup_trig":"figures/duration_inflation/cup_durinfl/POISONED_000000270605.pdf",
 "sp_mouse_clean":"figures/targeted_redirection/mouse_knife_TA/CLEAN_000000474401.pdf",
 "sp_mouse_trig":"figures/targeted_redirection/mouse_knife_TA/POISONED_000000474401.pdf",
 "sp_cup_clean":"figures/targeted_redirection/cup_knife/CLEAN_000000270605.pdf",
 "sp_cup_trig":"figures/targeted_redirection/cup_knife/POISONED_000000270605.pdf",
 "sp_mouse2_clean":"targeted_redirection/mouse_knife/CLEAN_000000063857.pdf",
 "sp_mouse2_trig":"targeted_redirection/mouse_knife/POISONED_000000063857.pdf",
}
out = {}
for k, rel in files.items():
    p = pymupdf.open(os.path.join(F, rel))[0]
    info = p.get_image_info()
    img = [list(i["bbox"]) for i in info]
    polys, marks = [], []
    for d in p.get_drawings():
        it = d["items"]; r = d["rect"]
        if d["type"] == "s" and it and all(x[0] == "l" for x in it) and len(it) >= 1 and r.width + r.height > 5:
            pts = [list(it[0][1])] + [list(x[2]) for x in it]
            polys.append({"pts": [[round(a,1),round(b,1)] for a,b in pts], "color": d.get("color"), "w": d.get("width")})
        if d["type"] == "fs" and len(it) in (4, 8) and 5 < r.width < 40 and abs(r.width - r.height) < 2:
            marks.append({"c": [round((r.x0+r.x1)/2,1), round((r.y0+r.y1)/2,1)], "r": round(r.width/2,1),
                          "shape": "circle" if len(it) == 8 else "diamond", "fill": [round(v,2) for v in d["fill"]]})
    out[k] = {"page": [p.rect.width, p.rect.height], "img": img, "polys": polys, "marks": marks}
    print(k, "img", [[round(v) for v in b] for b in img], "polys", [(len(q["pts"]), q["color"] and [round(c,2) for c in q["color"]]) for q in polys], "marks", [(m["c"], m["shape"], m["fill"]) for m in marks])
json.dump(out, open(sys.argv[2], "w"), indent=1)
