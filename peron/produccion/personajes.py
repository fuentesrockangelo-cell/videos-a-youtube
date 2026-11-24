"""Personajes de caricatura cabezona, con color fuerte y caras expresivas.

sprite(tipo, humor, ojos_cerrados, mira, luz) devuelve un RGBA de 520x780 (pies en (260, 760)).
Se dibuja al doble de tamaño y se reduce para que los bordes salgan suaves.
"""
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter

K = 2  # supermuestreo
SW, SH = 520, 780
PX, PY = 260, 760  # pies
OUT = (22, 16, 20)
LW = 7

PIEL = {"normal": (244, 196, 150), "morena": (214, 160, 115)}
TIPOS = {
    # traje, pelo, gorra, piel, extras
    "peron": dict(traje=(122, 132, 70), pelo=(24, 22, 28), gorra="militar", piel="normal", banda=True, sonrisa=True),
    "peron_viejo": dict(traje=(40, 44, 62), pelo=(190, 190, 196), gorra="militar", piel="normal", banda=True, arrugas=True),
    "evita": dict(traje=(245, 240, 232), pelo=(250, 205, 70), gorra=None, piel="normal", mujer=True, mono=True, labios=True),
    "mujer": dict(traje=(170, 50, 95), pelo=(90, 50, 30), gorra=None, piel="normal", mujer=True, labios=True),
    "soldado": dict(traje=(90, 120, 60), pelo=(50, 35, 25), gorra="casco", piel="morena"),
    "obrero": dict(traje=(45, 100, 190), pelo=(50, 35, 25), gorra="boina", piel="morena"),
    "juez": dict(traje=(28, 28, 36), pelo=(225, 225, 230), gorra=None, piel="normal", lentes=True, bigote=True),
    "policia": dict(traje=(30, 70, 170), pelo=(40, 30, 25), gorra="policia", piel="normal", bigote=True),
    "sereno": dict(traje=(130, 90, 50), pelo=(160, 160, 160), gorra="boina_cafe", piel="morena", bigote=True),
    "ladron": dict(traje=(28, 28, 34), pelo=(28, 28, 34), gorra="capucha", piel="normal", mascara=True),
    "encapuchado": dict(traje=(150, 20, 35), pelo=(150, 20, 35), gorra="capucha_punta", piel="sombra"),
}


def _osc(c, f=0.72):
    return tuple(int(v * f) for v in c)


def _cla(c, f=1.25):
    return tuple(min(255, int(v * f)) for v in c)


def _dibujar(tipo, humor, cerrados, brazos):
    cfg = TIPOS.get(tipo, TIPOS["peron"])
    img = Image.new("RGBA", (SW * K, SH * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(x, y):
        return (x * K, y * K)

    def E(box, **kw):
        x0, y0, x1, y1 = box
        if "width" in kw:
            kw["width"] = int(kw["width"] * K)
        d.ellipse([x0 * K, y0 * K, x1 * K, y1 * K], **kw)

    def R(box, r=0, **kw):
        x0, y0, x1, y1 = box
        if "width" in kw:
            kw["width"] = int(kw["width"] * K)
        d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], radius=int(r * K), **kw)

    def PG(pts, **kw):
        if "width" in kw:
            kw["width"] = int(kw["width"] * K)
        d.polygon([P(*p) for p in pts], **kw)

    def L(pts, w, fill):
        d.line([P(*p) for p in pts], fill=fill, width=int(w * K), joint="curve")
        for p in (pts[0], pts[-1]):
            E([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fill)

    piel = PIEL.get(cfg["piel"], (60, 20, 25))
    traje = cfg["traje"]
    cx = PX
    # ---------------- piernas y zapatos
    if not cfg.get("mujer") and tipo not in ("encapuchado",):
        for dx in (-34, 34):
            R([cx + dx - 26, 600, cx + dx + 26, PY - 18], 14, fill=_osc(traje, 0.6), outline=OUT, width=LW)
            E([cx + dx - 40, PY - 34, cx + dx + 44, PY + 2], fill=(25, 22, 24), outline=OUT, width=LW)
    elif cfg.get("mujer"):
        for dx in (-24, 24):
            R([cx + dx - 14, 650, cx + dx + 14, PY - 14], 8, fill=piel, outline=OUT, width=LW)
            E([cx + dx - 26, PY - 28, cx + dx + 30, PY + 2], fill=(180, 30, 40), outline=OUT, width=LW)
    # ---------------- cuerpo
    if cfg.get("mujer"):
        PG([(cx - 70, 400), (cx + 70, 400), (cx + 130, 680), (cx - 130, 680)], fill=traje, outline=OUT, width=LW)
        PG([(cx + 20, 410), (cx + 70, 400), (cx + 130, 680), (cx + 60, 680)], fill=_osc(traje, 0.85))
        PG([(cx - 70, 400), (cx + 70, 400), (cx + 130, 680), (cx - 130, 680)], outline=OUT, width=LW)
    elif tipo == "encapuchado":
        PG([(cx - 95, 390), (cx + 95, 390), (cx + 135, PY), (cx - 135, PY)], fill=traje, outline=OUT, width=LW)
        PG([(cx + 30, 395), (cx + 95, 390), (cx + 135, PY), (cx + 60, PY)], fill=_osc(traje, 0.75))
    elif tipo == "juez":
        R([cx - 95, 390, cx + 95, 640], 40, fill=traje, outline=OUT, width=LW)
        PG([(cx - 30, 395), (cx, 470), (cx + 30, 395)], fill=(245, 245, 245), outline=OUT, width=4)
        PG([(cx - 10, 420), (cx + 10, 420), (cx + 6, 500), (cx - 6, 500)], fill=(170, 30, 40))
    else:
        R([cx - 95, 390, cx + 95, 630], 44, fill=traje, outline=OUT, width=LW)
        R([cx + 25, 400, cx + 95, 630], 40, fill=_osc(traje, 0.82))
        R([cx - 95, 390, cx + 95, 630], 44, outline=OUT, width=LW)
        if tipo in ("peron", "peron_viejo", "soldado", "policia"):
            for i in range(4):
                E([cx - 8, 440 + i * 44, cx + 8, 456 + i * 44], fill=(250, 205, 60), outline=OUT, width=2)
            for sx in (-1, 1):  # charreteras
                R([cx + sx * 95 - 34, 392, cx + sx * 95 + 34, 412], 8, fill=(250, 205, 60), outline=OUT, width=3)
        if tipo == "obrero":
            R([cx - 55, 470, cx + 55, 630], 10, fill=(70, 130, 215), outline=OUT, width=4)
            for sx in (-40, 40):
                L([(cx + sx, 400), (cx + sx, 480)], 10, (70, 130, 215))
        if cfg.get("banda"):
            PG([(cx - 95, 410), (cx - 60, 392), (cx + 95, 590), (cx + 80, 626)], fill=(108, 172, 228), outline=OUT, width=4)
            PG([(cx - 80, 404), (cx - 70, 398), (cx + 88, 602), (cx + 84, 614)], fill=(250, 250, 250))
            E([cx - 22, 495, cx + 22, 539], fill=(250, 205, 60), outline=OUT, width=3)
    # ---------------- brazos
    poses = {"abajo": ((-150, 590), (150, 590)), "arriba": ((-170, 220), (170, 220)), "uno": ((-150, 590), (175, 230)),
             "frente": ((-150, 590), (235, 430)), "duda": ((-215, 380), (215, 380))}
    mi, md = poses.get(brazos, poses["abajo"])
    manga = traje if not cfg.get("mujer") else piel
    for (hx, hy), (mx, my) in (((cx - 85, 420), (cx + mi[0], mi[1])), ((cx + 85, 420), (cx + md[0], md[1]))):
        L([(hx, hy), (mx, my)], 46, OUT)
        L([(hx, hy), (mx, my)], 46 - LW * 2, manga)
        E([mx - 26, my - 26, mx + 26, my + 26], fill=piel if tipo != "encapuchado" else (30, 20, 25), outline=OUT, width=LW)
    if tipo == "soldado":
        L([(cx + 150, 650), (cx + 205, 250)], 16, (70, 50, 30))
    # ---------------- cabeza (grande)
    hx, hy, r = cx, 240, 150
    if cfg["gorra"] in ("capucha", "capucha_punta"):
        if cfg["gorra"] == "capucha_punta":
            PG([(hx - 150, hy + 40), (hx, hy - 260), (hx + 150, hy + 40)], fill=traje, outline=OUT, width=LW)
        E([hx - r - 20, hy - r - 20, hx + r + 20, hy + r + 30], fill=traje, outline=OUT, width=LW)
    if cfg.get("mono"):
        E([hx - 110, hy - 245, hx + 70, hy - 95], fill=cfg["pelo"], outline=OUT, width=LW)
        E([hx - 80, hy - 225, hx - 20, hy - 180], fill=_cla(cfg["pelo"], 1.15))
    if cfg.get("mujer") and not cfg.get("mono"):
        R([hx - r - 18, hy - 60, hx + r + 18, hy + 190], 60, fill=cfg["pelo"], outline=OUT, width=LW)
    cara = piel if tipo != "encapuchado" else (25, 12, 16)
    E([hx - r, hy - r, hx + r, hy + r], fill=cara, outline=OUT, width=LW)
    if tipo != "encapuchado":
        d.chord([(hx - r + 18) * K, (hy - r + 10) * K, (hx + r - 6) * K, (hy + r - 4) * K], 300, 60, fill=_osc(piel, 0.86))  # sombra lateral
        E([hx - r - 6, hy - 10, hx - r + 30, hy + 50], fill=piel, outline=OUT, width=LW)  # oreja
    # pelo
    if cfg["gorra"] not in ("capucha", "capucha_punta"):
        pelo = cfg["pelo"]
        if cfg.get("mujer"):
            d.chord([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy - r * 0.15) * K], 180, 360, fill=pelo, outline=OUT, width=LW * K)
            E([hx - 90, hy - 138, hx - 10, hy - 112], fill=_cla(pelo, 1.2))
        else:
            d.chord([(hx - r) * K, (hy - r) * K, (hx + r) * K, (hy - r * 0.25) * K], 180, 360, fill=pelo, outline=OUT, width=LW * K)
            E([hx - 80, hy - 138, hx + 10, hy - 118], fill=_cla(pelo, 2.2) if sum(pelo) < 150 else _cla(pelo, 1.1))  # brillo engominado
    # gorras
    g = cfg["gorra"]
    if g in ("militar", "policia"):
        col = (110, 120, 66) if g == "militar" else (25, 55, 140)
        b = hy - 118  # base de la gorra sobre la frente
        PG([(hx - 140, b), (hx - 175, b - 120), (hx + 180, b - 132), (hx + 145, b)], fill=col, outline=OUT, width=LW)
        PG([(hx + 30, b - 126), (hx + 180, b - 132), (hx + 145, b), (hx + 40, b)], fill=_osc(col, 0.8))
        PG([(hx - 140, b), (hx - 175, b - 120), (hx + 180, b - 132), (hx + 145, b)], outline=OUT, width=LW)
        R([hx - 146, b - 26, hx + 150, b + 4], 6, fill=(250, 205, 60) if g == "militar" else (20, 20, 25), outline=OUT, width=4)
        E([hx - 26, b - 104, hx + 26, b - 52], fill=(250, 205, 60), outline=OUT, width=4)
        PG([(hx - 40, b + 2), (hx + 200, b + 12), (hx + 178, b + 36), (hx - 20, b + 22)], fill=(18, 18, 22), outline=OUT, width=4)
    elif g == "casco":
        d.chord([(hx - r - 15) * K, (hy - r - 30) * K, (hx + r + 15) * K, (hy - 40) * K], 180, 360, fill=(80, 110, 55), outline=OUT, width=LW * K)
    elif g in ("boina", "boina_cafe"):
        col = (45, 100, 190) if g == "boina" else (110, 75, 40)
        d.chord([(hx - r + 5) * K, (hy - r - 30) * K, (hx + r - 5) * K, (hy - 60) * K], 180, 360, fill=col, outline=OUT, width=LW * K)
        PG([(hx + 30, hy - 100), (hx + 195, hy - 88), (hx + 160, hy - 70), (hx + 20, hy - 82)], fill=_osc(col), outline=OUT, width=4)
    # ---------------- cara
    ey = hy + 5
    feliz = humor == "feliz"; susto = humor == "susto"; enojo = humor == "enojo"; triste = humor == "triste"
    if tipo == "encapuchado":
        for ex in (hx - 50, hx + 50):
            E([ex - 28, ey - 14, ex + 28, ey + 14], fill=(255, 60, 40))
            E([ex - 12, ey - 7, ex + 12, ey + 7], fill=(255, 230, 160))
    else:
        for i, ex in enumerate((hx - 52, hx + 58)):
            rw, rh = (40, 46) if not susto else (46, 54)
            if cerrados:
                d.arc([(ex - rw) * K, (ey - 20) * K, (ex + rw) * K, (ey + 24) * K], 10, 170, fill=OUT, width=6 * K)
            else:
                E([ex - rw, ey - rh, ex + rw, ey + rh], fill=(255, 255, 255), outline=OUT, width=LW)
                ir = 22 if not susto else 15
                ix = ex + 8
                E([ix - ir, ey - ir + 4, ix + ir, ey + ir + 4], fill=(70, 45, 30))
                E([ix - ir * 0.55, ey - ir * 0.55 + 4, ix + ir * 0.55, ey + ir * 0.55 + 4], fill=(10, 8, 10))
                E([ix - 14, ey - 16, ix - 2, ey - 4], fill=(255, 255, 255))
                E([ix + 6, ey + 8, ix + 12, ey + 14], fill=(255, 255, 255))
            # cejas
            by = ey - 70
            if enojo:
                pts = [(ex - 40, by - 8 if i == 0 else by + 14), (ex + 40, by + 14 if i == 0 else by - 8)]
            elif triste or susto:
                pts = [(ex - 40, by + 12 if i == 0 else by - 14), (ex + 40, by - 14 if i == 0 else by + 12)]
                if susto:
                    pts = [(ex - 40, by - 12), (ex + 40, by - 18)]
            else:
                pts = [(ex - 40, by + 2), (ex + 40, by - 6)]
            L(pts, 16, cfg["pelo"] if sum(cfg["pelo"]) < 400 else _osc(cfg["pelo"], 0.6))
        if cfg.get("lentes"):
            for ex in (hx - 52, hx + 58):
                E([ex - 50, ey - 50, ex + 50, ey + 50], outline=OUT, width=6)
            L([(hx - 2, ey), (hx + 8, ey)], 6, OUT)
        # nariz
        E([hx + 2, ey + 34, hx + 46, ey + 70], fill=_osc(piel, 0.9), outline=OUT, width=5)
        # mejillas
        if not cfg.get("mascara"):
            E([hx - 118, ey + 52, hx - 72, ey + 80], fill=(240, 130, 120))
            E([hx + 88, ey + 52, hx + 134, ey + 80], fill=(240, 130, 120))
        my = ey + 98
        if cfg.get("mascara"):
            d.chord([(hx - r + 4) * K, (hy - 30) * K, (hx + r - 4) * K, (hy + r) * K], 0, 180, fill=(20, 20, 26))
            R([hx - r + 4, ey + 30, hx + r - 4, ey + 60], 10, fill=(20, 20, 26))
        elif feliz or (cfg.get("sonrisa") and humor == "normal"):
            d.chord([(hx - 62) * K, (my - 40) * K, (hx + 62) * K, (my + 46) * K], 0, 180, fill=(120, 25, 35), outline=OUT, width=6 * K)
            R([hx - 50, my, hx + 50, my + 16], 4, fill=(255, 255, 255))
            if cfg.get("labios"):
                d.arc([(hx - 62) * K, (my - 40) * K, (hx + 62) * K, (my + 46) * K], 0, 180, fill=(215, 30, 50), width=8 * K)
        elif susto:
            E([hx - 26, my - 14, hx + 26, my + 46], fill=(90, 15, 25), outline=OUT, width=6)
        elif enojo or triste:
            d.arc([(hx - 40) * K, (my) * K, (hx + 40) * K, (my + 40) * K], 200, 340, fill=OUT, width=7 * K)
        else:
            L([(hx - 30, my + 10), (hx + 30, my + 6)], 8, (215, 30, 50) if cfg.get("labios") else OUT)
        if cfg.get("bigote"):
            PG([(hx - 50, my - 8), (hx, my - 24), (hx + 50, my - 8), (hx + 40, my + 4), (hx, my - 8), (hx - 40, my + 4)],
               fill=_osc(cfg["pelo"], 0.8), outline=OUT, width=4)
        if cfg.get("arrugas"):
            for k in range(2):
                d.arc([(hx - 70) * K, (hy - 120 + k * 16) * K, (hx + 70) * K, (hy - 60 + k * 16) * K], 200, 340, fill=_osc(piel, 0.7), width=4 * K)
    return img.resize((SW, SH), Image.LANCZOS)


@lru_cache(maxsize=256)
def sprite(tipo, humor="normal", cerrados=False, brazos="abajo", mira=1, luz=(255, 200, 140)):
    """Sprite final con borde de luz de color y halo suave."""
    base = _dibujar(tipo, humor, cerrados, brazos)
    if mira < 0:
        base = base.transpose(Image.FLIP_LEFT_RIGHT)
    a = base.getchannel("A")
    pad = 40
    out = Image.new("RGBA", (SW + pad * 2, SH + pad * 2), (0, 0, 0, 0))
    halo = Image.new("L", out.size, 0)
    halo.paste(a, (pad, pad))
    halo = halo.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55))
    out.paste(Image.new("RGBA", out.size, luz + (255,)), (0, 0), halo)
    rim = Image.new("L", out.size, 0)
    rim.paste(a, (pad - 3 * mira, pad - 3))
    out.paste(Image.new("RGBA", out.size, luz + (255,)), (0, 0), rim.filter(ImageFilter.GaussianBlur(2)))
    out.alpha_composite(base, (pad, pad))
    return out


PIES = (PX + 40, PY + 40)  # posición de los pies dentro del sprite con margen
