"""Arma el video con monigotes, cabecera y subtítulos karaoke.

Uso: python3 video.py <dir_con_voz_y_tiempos> <salida.mp4> <vertical|horizontal> <final: parte1|encuesta|suscribete>
Fuentes: variable FONTS_DIR con fontsource-anton.woff y fontsource-bebas-neue.woff
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FD = os.environ["FONTS_DIR"]
ANTON = os.path.join(FD, "fontsource-anton.woff")
BEBAS = os.path.join(FD, "fontsource-bebas-neue.woff")
ELITE = os.path.join(FD, "fontsource-special-elite.woff")
FPS = 25
LABEL_Y = 0.075
ROJO = (214, 32, 39); BLANCO = (245, 245, 245); NEGRO = (12, 12, 14); AMAR = (250, 204, 21)
PIEL = (243, 205, 160); OUT = (20, 20, 20)


def F(path, size, _c={}):
    k = (path, size)
    if k not in _c:
        _c[k] = ImageFont.truetype(path, size)
    return _c[k]


# ---------------------------------------------------------------- personajes
def ojos(d, x, y, s, mirada=0, susto=False):
    r = 13 * s if not susto else 16 * s
    for dx in (-18 * s, 18 * s):
        d.ellipse([x + dx - r, y - r, x + dx + r, y + r], fill="white", outline=OUT, width=int(3 * s))
        pr = 5 * s
        d.ellipse([x + dx - pr + mirada * s, y - pr, x + dx + pr + mirada * s, y + pr], fill=OUT)


RIM = (255, 214, 160)


def _figura(md, x, y, s, tipo, brazos, m):
    """Dibuja la silueta en una máscara. m = 1 mira a la derecha, -1 a la izquierda."""
    def P(dx, dy):
        return (x + dx * m * s, y + dy * s)
    def poly(pts):
        md.polygon([P(*q) for q in pts], fill=255)
    def ell(cx, cy, rx, ry):
        a, b = P(cx - rx * m, cy - ry), P(cx + rx * m, cy + ry)
        md.ellipse([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], fill=255)
    def linea(p1, p2, w):
        md.line([P(*p1), P(*p2)], fill=255, width=int(w * s))
        for q in (p1, p2):
            ell(q[0], q[1], w / 2, w / 2)
    largo = tipo in ("juez", "encapuchado", "evita", "mujer", "ladron")
    # piernas
    if not largo or tipo == "ladron":
        linea((-18, -170), (-24, -8), 30); linea((18, -170), (26, -8), 30)
        ell(-18, -6, 26, 10); ell(34, -6, 26, 10)
    # torso / abrigo
    if tipo in ("evita", "mujer"):
        poly([(-40, -330), (40, -330), (55, -250), (95, -20), (-95, -20), (-55, -250)])
        linea((-14, -30), (-14, 0), 18); linea((14, -30), (14, 0), 18)
    elif tipo in ("juez", "encapuchado"):
        poly([(-58, -335), (58, -335), (82, 0), (-82, 0)])
    else:
        poly([(-60, -330), (60, -330), (66, -290), (50, -165), (-50, -165), (-66, -290)])
        ell(0, -318, 66, 26)
        if tipo in ("peron", "peron_viejo", "soldado", "policia", "sereno"):  # faldón de saco
            poly([(-58, -175), (58, -175), (54, -130), (-54, -130)])
    # cuello y cabeza
    poly([(-16, -350), (16, -350), (18, -330), (-18, -330)])
    hy = -398
    if tipo in ("encapuchado", "ladron"):
        ell(0, hy, 50, 56)
        if tipo == "encapuchado":
            poly([(-48, hy - 10), (0, hy - 120), (50, hy - 10)])
    else:
        ell(0, hy, 44, 50)
        poly([(36, hy - 10), (58, hy + 8), (40, hy + 16)])  # nariz
        poly([(20, hy + 30), (36, hy + 34), (24, hy + 50), (0, hy + 50)])  # mentón
        if tipo in ("peron", "peron_viejo", "soldado", "policia"):  # gorra de plato con visera
            poly([(-46, hy - 26), (-62, hy - 80), (56, hy - 88), (46, hy - 30)])
            ell(-3, hy - 84, 59, 10)
            poly([(26, hy - 36), (84, hy - 22), (80, hy - 14), (16, hy - 22)])
        elif tipo == "evita":
            ell(-38, hy - 18, 34, 32)  # moño
        elif tipo == "mujer":
            poly([(-48, hy - 30), (36, hy - 40), (40, hy + 10), (-30, hy + 90), (-60, hy + 40)])
        elif tipo == "obrero":
            poly([(-46, hy - 26), (0, hy - 60), (46, hy - 30), (80, hy - 20), (40, hy - 16)])
        elif tipo == "sereno":
            poly([(-50, hy - 30), (-40, hy - 70), (44, hy - 70), (52, hy - 30), (70, hy - 24), (-60, hy - 24)])
        elif tipo == "juez":
            ell(-6, hy - 8, 50, 50)
    # brazos
    hombro_d, hombro_i = (52, -318), (-52, -318)
    poses = {"abajo": ((-58, -170), (62, -170)), "arriba": ((-90, -500), (95, -500)),
             "uno": ((-58, -170), (135, -505)), "frente": ((-58, -170), (175, -300)),
             "duda": ((-120, -300), (125, -300))}
    mi, mdx = poses.get(brazos, poses["abajo"])
    codo_i = ((hombro_i[0] + mi[0]) / 2 - 12, (hombro_i[1] + mi[1]) / 2 + 6)
    codo_d = ((hombro_d[0] + mdx[0]) / 2 + 12, (hombro_d[1] + mdx[1]) / 2 + 6)
    for h, c, mano_ in ((hombro_i, codo_i, mi), (hombro_d, codo_d, mdx)):
        linea(h, c, 34); linea(c, mano_, 26); ell(mano_[0], mano_[1], 17, 17)
    if tipo == "soldado":
        linea((80, -120), (110, -470), 12)
    return hy


def monigote(d, x, y, s=1.0, tipo="peron", brazos="abajo", boca="normal", susto=False, mira=1, luz=RIM):
    """Silueta noir a contraluz. x,y = pies. Altura ~ 520*s."""
    img = d._image
    s *= 1.0
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    hy = _figura(md, x, y, s, tipo, brazos, mira)
    mask = mask.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: min(255, int(v * 1.6)))
    # halo detrás
    halo = mask.filter(ImageFilter.GaussianBlur(int(28 * s) + 1)).point(lambda v: int(v * 0.45))
    img.paste(Image.new("RGB", (W, H), tuple(int(c * 0.55) for c in luz)), (0, 0), halo)
    # borde de luz (contraluz desde arriba-izquierda)
    off = max(2, int(5 * s))
    rim = ImageChops.offset(mask, -off * mira, -off).filter(ImageFilter.GaussianBlur(1.2))
    img.paste(Image.new("RGB", (W, H), luz), (0, 0), rim)
    # cuerpo negro
    img.paste(Image.new("RGB", (W, H), (10, 10, 13)), (0, 0), mask)
    d2 = ImageDraw.Draw(img)
    # sombra en el piso
    d2.ellipse([x - 110 * s, y - 8 * s, x + 110 * s, y + 16 * s], fill=(6, 6, 8))
    # detalles con luz: ojos de los malos, banda presidencial, linterna, insignias
    if tipo in ("ladron", "encapuchado"):
        for dx in (-14, 16):
            ex, ey = x + dx * mira * s + 12 * mira * s, y + (hy - 4) * s
            glow(img, [([ex - 16 * s, ey - 10 * s, ex + 16 * s, ey + 10 * s], (200, 20, 20), "ellipse")], int(8 * s) + 1)
            d2.ellipse([ex - 7 * s, ey - 4 * s, ex + 7 * s, ey + 4 * s], fill=(255, 70, 60))
    if tipo == "peron":
        d2.line([(x - 50 * mira * s, y - 330 * s), (x + 55 * mira * s, y - 175 * s)], fill=(105, 150, 200), width=int(14 * s))
        d2.line([(x - 50 * mira * s, y - 330 * s), (x + 55 * mira * s, y - 175 * s)], fill=(210, 220, 230), width=int(4 * s))
    if tipo in ("peron", "peron_viejo", "soldado", "policia"):
        d2.ellipse([x + 4 * mira * s - 6 * s, y + (hy - 62) * s, x + 4 * mira * s + 6 * s, y + (hy - 50) * s], fill=(230, 180, 60))
    if tipo == "sereno":
        lx, ly = x + 175 * mira * s, y - 290 * s
        glow(img, [([lx - 90 * s, ly - 90 * s, lx + 90 * s, ly + 90 * s], (200, 140, 40), "ellipse")], int(30 * s))
        d2.rectangle([lx - 14 * s, ly - 10 * s, lx + 14 * s, ly + 26 * s], fill=(255, 210, 110), outline=(10, 10, 13), width=3)
    if tipo == "juez":
        d2.rectangle([x + 150 * mira * s - 30 * s, y - 330 * s, x + 150 * mira * s + 30 * s, y - 300 * s], fill=(10, 10, 13))
    if susto or boca == "o":
        pass


# ---------------------------------------------------------------- fondos
def glow(img, shapes, radius, strength=1.0):
    """Suma luz difusa: shapes = [(bbox, color, 'ellipse'|'polygon'|'rect')]."""
    W, H = img.size
    lay = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(lay)
    for geom, col, kind in shapes:
        col = tuple(int(c * strength) for c in col)
        getattr(gd, kind)(geom, fill=col)
    lay = lay.filter(ImageFilter.GaussianBlur(radius))
    img.paste(ImageChops.add(img, lay))


def cielo(d, W, H, top, bot, hasta):
    for i in range(hasta):
        t = i / max(1, hasta)
        d.line([(0, i), (W, i)], fill=tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3)))


def estrellas(d, W, H, n=90, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.55))
        r = rnd.choice((1, 1, 2, 2, 3))
        c = rnd.randint(150, 235)
        d.ellipse([x, y, x + r, y + r], fill=(c, c, c + 10 if c < 245 else c))


def fondo(img, tipo):
    W, H = img.size
    d = ImageDraw.Draw(img)
    piso = int(H * 0.82)
    luces = []
    if tipo in ("noche", "isla", "plaza"):
        cielo(d, W, H, (8, 10, 24), (28, 36, 62), H)
        estrellas(d, W, H)
        mx, my, mr = W * 0.86, H * 0.16, 52
        d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(205, 205, 190))
        d.ellipse([mx - mr * 0.5, my - mr * 0.3, mx - mr * 0.2, my], fill=(200, 200, 185))
        luces.append(([mx - mr * 2.2, my - mr * 2.2, mx + mr * 2.2, my + mr * 2.2], (70, 70, 60), "ellipse"))
    if tipo == "noche":
        d.rectangle([0, piso - 70, W, piso], fill=(62, 52, 40))  # muro bajo
        for xx in range(0, W, 90):
            d.line([(xx, piso - 70), (xx, piso)], fill=(50, 42, 33), width=3)
        d.rectangle([0, piso, W, H], fill=(38, 38, 40))
    elif tipo == "isla":
        d.rectangle([0, int(H * 0.62), W, H], fill=(14, 24, 44))
        for k in range(10):
            yy = int(H * 0.66) + k * 34
            d.line([(0, yy), (W, yy + 6)], fill=(30, 46, 75), width=2)
        luces.append(([W * 0.78, H * 0.62, W * 0.9, H], (60, 60, 50), "rectangle"))
    elif tipo == "plaza":
        bx = W // 2
        d.rectangle([bx - 320, piso - 340, bx + 320, piso], fill=(120, 80, 85), outline=(25, 20, 22), width=4)
        d.polygon([(bx - 120, piso - 340), (bx, piso - 420), (bx + 120, piso - 340)], fill=(110, 72, 78), outline=(25, 20, 22))
        for i in range(-260, 270, 104):
            for row in (0, 1):
                y0 = piso - 290 + row * 120
                d.rectangle([bx + i - 24, y0, bx + i + 24, y0 + 70], fill=(240, 200, 110))
                luces.append(([bx + i - 40, y0 - 15, bx + i + 40, y0 + 85], (150, 110, 40), "rectangle"))
        d.rectangle([0, piso, W, H], fill=(40, 40, 44))
    elif tipo == "cripta":
        d.rectangle([0, 0, W, H], fill=(34, 32, 32))
        for yy in range(0, piso, 60):
            off = 0 if (yy // 60) % 2 else 60
            for xx in range(-off, W, 120):
                d.rectangle([xx, yy, xx + 118, yy + 58], fill=(44, 41, 40), outline=(26, 24, 24), width=3)
        d.rectangle([0, piso, W, H], fill=(22, 20, 20))
        for cx in (W * 0.12, W * 0.88):  # velas
            d.rectangle([cx - 12, piso - 110, cx + 12, piso - 40], fill=(220, 210, 190))
            d.ellipse([cx - 10, piso - 140, cx + 10, piso - 108], fill=(255, 200, 90))
            luces.append(([cx - 260, piso - 380, cx + 260, piso + 120], (150, 85, 25), "ellipse"))
    elif tipo == "oficina":
        d.rectangle([0, 0, W, H], fill=(38, 28, 22))
        for xx in range(0, W, 46):
            d.line([(xx, 0), (xx, piso)], fill=(30, 22, 17), width=3)
        d.rectangle([0, piso, W, H], fill=(24, 17, 13))
        lx = W * 0.5
        d.polygon([(lx - 60, 0), (lx + 60, 0), (lx + 40, 40), (lx - 40, 40)], fill=(30, 50, 40))
        luces.append(([(lx - 50, 40), (lx + 50, 40), (lx + W * 0.42, piso + 40), (lx - W * 0.42, piso + 40)], (110, 85, 40), "polygon"))
    elif tipo not in ("noche", "isla", "plaza"):  # oscuro con viñeta roja
        d.rectangle([0, 0, W, H], fill=NEGRO)
        luces.append(([W * 0.15, H * 0.12, W * 0.85, H * 0.88], (120, 14, 20), "ellipse"))
    if luces:
        glow(img, luces, max(30, min(W, H) // 12))
    return piso


def etiqueta(d, x, y, txt, size=46, fg=(235, 60, 60), bg=(10, 10, 12)):
    f = F(ELITE, size)
    w = d.textlength(txt, font=f)
    d.rectangle([x - w / 2 - 18, y - 8, x + w / 2 + 18, y + size + 8], fill=bg, outline=ROJO, width=4)
    d.text((x - w / 2, y), txt, font=f, fill=fg)


def signo(d, x, y, size=120, ch="?", col=ROJO):
    f = F(ANTON, size)
    d.text((x, y), ch, font=f, fill=col, stroke_width=4, stroke_fill=OUT, anchor="mm")


def ataud(d, x, y, s=1.0, vidrio=True, roto=False, manos=False):
    d.polygon([(x - 260 * s, y - 70 * s), (x + 260 * s, y - 70 * s), (x + 230 * s, y), (x - 230 * s, y)], fill=(90, 50, 25), outline=OUT)
    d.rectangle([x - 260 * s, y - 120 * s, x + 260 * s, y - 70 * s], fill=(120, 70, 35), outline=OUT, width=4)
    if vidrio:
        d.rectangle([x - 240 * s, y - 220 * s, x + 240 * s, y - 120 * s], fill=(170, 210, 230), outline=(230, 240, 250), width=6)
        d.line([(x - 200 * s, y - 210 * s), (x - 150 * s, y - 130 * s)], fill="white", width=4)
        if roto:
            cx, cy = x + 60 * s, y - 170 * s
            d.ellipse([cx - 45 * s, cy - 35 * s, cx + 45 * s, cy + 35 * s], fill=(20, 20, 20))
            for a in range(0, 360, 45):
                d.line([(cx, cy), (cx + math.cos(math.radians(a)) * 110 * s, cy + math.sin(math.radians(a)) * 60 * s)], fill="white", width=3)
    if manos:
        for dx in (-70, 70):
            signo(d, x + dx * s, y - 300 * s, int(110 * s))


def mano(d, x, y, s=1.0, col=PIEL):
    d.rounded_rectangle([x - 40 * s, y - 30 * s, x + 40 * s, y + 50 * s], radius=int(20 * s), fill=col, outline=OUT, width=4)
    for i, h in enumerate((70, 85, 80, 65)):
        xx = x - 36 * s + i * 22 * s
        d.rounded_rectangle([xx, y - h * s, xx + 18 * s, y - 20 * s], radius=int(9 * s), fill=col, outline=OUT, width=3)
    d.rounded_rectangle([x + 38 * s, y - 20 * s, x + 75 * s, y + 5 * s], radius=int(10 * s), fill=col, outline=OUT, width=3)


def sobre(d, x, y, s=1.0, txt=None):
    d.rectangle([x - 110 * s, y - 70 * s, x + 110 * s, y + 70 * s], fill=(240, 230, 205), outline=OUT, width=4)
    d.line([(x - 110 * s, y - 70 * s), (x, y + 5 * s), (x + 110 * s, y - 70 * s)], fill=OUT, width=4)
    if txt:
        d.text((x, y + 40 * s), txt, font=F(BEBAS, int(30 * s)), fill=ROJO, anchor="mm")


def post(img):
    """Gradación tipo cómic nocturno: menos saturación, contraste, textura de papel y viñeta."""
    from PIL import ImageEnhance
    W, H = img.size
    img = ImageEnhance.Color(img).enhance(0.78)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    rnd = random.Random(11)
    tex = Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).convert("RGB")
    img = Image.blend(img, ImageChops.multiply(img, ImageChops.invert(ImageChops.invert(tex).point(lambda v: v // 3))), 0.35)
    return ImageChops.multiply(img, vignette(W, H, 0.62))


def vignette(W, H, fuerza, _c={}):
    k = (W, H, fuerza)
    if k not in _c:
        m = Image.new("L", (W // 4, H // 4), 0)
        ImageDraw.Draw(m).ellipse([-W * 0.08, -H * 0.06, W * 0.33, H * 0.31], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(W // 18)).resize((W, H))
        m = m.point(lambda v: int(255 * (1 - fuerza) + v * fuerza))
        _c[k] = Image.merge("RGB", (m, m, m))
    return _c[k]


def escena(tipo, W, H):
    img = Image.new("RGB", (W, H))
    cx = W // 2
    fondos = {"pueblo": "noche", "ejercito": "plaza", "isla": "isla", "multitud": "plaza", "presidente": "plaza",
              "evita": "plaza", "evita_oculta": "noche", "exilio": "oscuro", "muerte": "oscuro", "ataud": "cripta",
              "vidrio": "cripta", "cementerio": "noche", "corte": "cripta", "sable": "cripta", "cartas": "oficina",
              "papel": "oficina", "juez": "oficina", "choque": "noche", "comisario": "oficina", "sereno": "noche",
              "llaves": "oficina", "expedientes": "oficina", "suiza": "oscuro", "logia": "oscuro", "adn": "oscuro",
              "traslado": "noche", "pregunta": "oscuro", "comenta": "oscuro", "encuesta": "oscuro", "suscribete": "oscuro",
              "dinero": "oficina", "peron": "oscuro", "ladron": "cripta"}
    piso = fondo(img, fondos.get(tipo, "oscuro"))
    d = ImageDraw.Draw(img)
    s = min(W, H * 1.2) / 1000
    if tipo == "pueblo":
        for i, bx in enumerate(range(int(cx - 420 * s), int(cx + 420 * s), int(210 * s))):
            d.rectangle([bx, piso - 160 * s, bx + 170 * s, piso], fill=(150, 120, 90), outline=OUT, width=4)
            d.polygon([(bx - 10 * s, piso - 160 * s), (bx + 85 * s, piso - 230 * s), (bx + 180 * s, piso - 160 * s)], fill=(120, 50, 40), outline=OUT)
        monigote(d, cx, piso + 10 * s, 0.7 * s, "obrero", boca="sonrisa")
        etiqueta(d, cx, H * LABEL_Y, "LOBOS · 1895")
    elif tipo == "ejercito":
        for dx in (-280, 280):
            monigote(d, cx + dx * s, piso + 10 * s, 0.75 * s, "soldado")
        monigote(d, cx, piso + 10 * s, 0.9 * s, "soldado", brazos="frente")
        etiqueta(d, cx, H * LABEL_Y, "1943")
    elif tipo == "isla":
        d.ellipse([cx - 300 * s, H * 0.55, cx + 300 * s, H * 0.75], fill=(200, 180, 120), outline=OUT, width=4)
        monigote(d, cx, H * 0.64, 0.6 * s, "peron", susto=True)
        etiqueta(d, cx, H * LABEL_Y, "OCTUBRE 1945")
    elif tipo == "multitud":
        rnd = random.Random(5)
        for row in range(3):
            for k in range(9):
                x = cx - 560 * s + k * 140 * s + (row % 2) * 70 * s
                monigote(d, x, piso + (60 + row * 70) * s, (0.32 + row * 0.06) * s, "obrero", brazos="arriba", boca="o")
        etiqueta(d, cx, H * LABEL_Y, "17 DE OCTUBRE")
    elif tipo == "presidente":
        monigote(d, cx, piso + 10 * s, 0.95 * s, "peron", brazos="arriba", boca="sonrisa")
        etiqueta(d, cx, H * LABEL_Y, "PRESIDENTE")
    elif tipo == "evita":
        monigote(d, cx - 150 * s, piso + 10 * s, 0.9 * s, "peron", boca="sonrisa")
        monigote(d, cx + 150 * s, piso + 10 * s, 0.85 * s, "evita", brazos="uno", boca="sonrisa")
        etiqueta(d, cx, H * LABEL_Y, "EVA DUARTE · EVITA")
    elif tipo == "evita_oculta":
        d.rectangle([cx - 230 * s, piso - 110 * s, cx + 230 * s, piso], fill=(90, 60, 40), outline=OUT, width=4)
        signo(d, cx, piso - 260 * s, int(200 * s))
        monigote(d, cx + 330 * s, piso + 10 * s, 0.6 * s, "soldado")
        etiqueta(d, cx, H * LABEL_Y, "CUERPO ESCONDIDO")
    elif tipo == "exilio":
        paises = ["PARAGUAY", "PANAMÁ", "VENEZUELA", "R. DOMINICANA", "ESPAÑA"]
        for i, p in enumerate(paises):
            etiqueta(d, cx - 250 * s + (i % 2) * 500 * s, (160 + i * 120) * s, p, size=int(44 * s), bg=(40, 40, 50))
        monigote(d, cx, piso + 10 * s, 0.7 * s, "peron")
        etiqueta(d, cx, H * LABEL_Y, "18 AÑOS DE EXILIO")
    elif tipo == "muerte":
        monigote(d, cx, piso + 10 * s, 0.9 * s, "peron_viejo")
        etiqueta(d, cx, H * LABEL_Y, "1 DE JULIO DE 1974")
    elif tipo in ("ataud", "vidrio"):
        ataud(d, cx, piso, 1.1 * s)
        etiqueta(d, cx, H * LABEL_Y, "VIDRIO BLINDADO · 8 CM" if tipo == "vidrio" else "CEMENTERIO DE LA CHACARITA")
    elif tipo == "cementerio":
        for k, dx in enumerate((-380, -150, 380)):
            d.rectangle([cx + dx * s - 30 * s, piso - 170 * s, cx + dx * s + 30 * s, piso], fill=(130, 130, 135), outline=OUT, width=4)
            d.rectangle([cx + dx * s - 80 * s, piso - 140 * s, cx + dx * s + 80 * s, piso - 100 * s], fill=(130, 130, 135), outline=OUT, width=4)
        monigote(d, cx + 130 * s, piso + 10 * s, 0.85 * s, "ladron")
        etiqueta(d, cx, H * LABEL_Y, "JUNIO DE 1987")
    elif tipo == "ladron":
        ataud(d, cx - 120 * s, piso, 0.9 * s, roto=True)
        monigote(d, cx + 270 * s, piso + 10 * s, 0.8 * s, "ladron", brazos="frente")
    elif tipo == "corte":
        ataud(d, cx, piso, 1.0 * s, roto=True, manos=True)
        # sierra
        d.polygon([(cx - 330 * s, 180 * s), (cx + 120 * s, 180 * s), (cx + 120 * s, 250 * s), (cx - 330 * s, 250 * s)], fill=(190, 190, 200), outline=OUT)
        for k in range(18):
            xx = cx - 330 * s + k * 25 * s
            d.polygon([(xx, 250 * s), (xx + 12 * s, 275 * s), (xx + 25 * s, 250 * s)], fill=(190, 190, 200), outline=OUT)
        d.rounded_rectangle([cx + 110 * s, 160 * s, cx + 220 * s, 270 * s], radius=int(20 * s), fill=(150, 40, 30), outline=OUT, width=4)
        etiqueta(d, cx, H * LABEL_Y, "LE CORTAN LAS MANOS")
    elif tipo == "sable":
        d.line([(cx - 300 * s, piso - 300 * s), (cx + 260 * s, piso - 420 * s)], fill=(210, 210, 220), width=int(22 * s))
        d.rectangle([cx - 360 * s, piso - 320 * s, cx - 290 * s, piso - 270 * s], fill=AMAR, outline=OUT, width=4)
        signo(d, cx, piso - 150 * s, int(160 * s))
        etiqueta(d, cx, H * LABEL_Y, "TAMBIÉN SU SABLE")
    elif tipo in ("cartas", "dinero"):
        for k, (dx, dy) in enumerate(((-280, 0), (0, -40), (280, 0))):
            sobre(d, cx + dx * s, piso - 300 * s + dy * s, 1.0 * s, "HERMES IAI Y LOS 13")
        f = F(ANTON, int(130 * s))
        d.text((cx, piso - 90 * s), "$8.000.000", font=f, fill=(90, 220, 90), stroke_width=5, stroke_fill=OUT, anchor="mm")
        etiqueta(d, cx, H * LABEL_Y, "PIDEN RESCATE")
    elif tipo == "papel":
        d.polygon([(cx - 200 * s, piso - 450 * s), (cx + 160 * s, piso - 470 * s), (cx + 200 * s, piso - 120 * s),
                   (cx + 40 * s, piso - 160 * s), (cx - 180 * s, piso - 110 * s)], fill=(245, 240, 220), outline=OUT)
        for k in range(6):
            d.line([(cx - 150 * s, piso - (420 - k * 45) * s), (cx + 140 * s, piso - (430 - k * 45) * s)], fill=(80, 80, 120), width=3)
        etiqueta(d, cx, H * LABEL_Y, "UN TROZO DE LA CARTA DE ISABEL")
    elif tipo == "juez":
        d.rectangle([cx - 350 * s, piso - 160 * s, cx + 350 * s, piso], fill=(90, 55, 30), outline=OUT, width=4)
        monigote(d, cx, piso - 120 * s, 0.75 * s, "juez")
        etiqueta(d, cx, H * LABEL_Y, "JUEZ JAIME FAR SUAU")
    elif tipo == "choque":
        d.rounded_rectangle([cx - 230 * s, piso - 170 * s, cx + 200 * s, piso - 40 * s], radius=int(30 * s), fill=(160, 30, 30), outline=OUT, width=5)
        for dx in (-140, 120):
            d.ellipse([cx + dx * s - 45 * s, piso - 85 * s, cx + dx * s + 45 * s, piso + 5 * s], fill=OUT)
        for a in range(0, 360, 30):
            d.line([(cx + 230 * s, piso - 120 * s), (cx + 230 * s + math.cos(math.radians(a)) * 90 * s, piso - 120 * s + math.sin(math.radians(a)) * 90 * s)], fill=AMAR, width=6)
        etiqueta(d, cx, H * LABEL_Y, "NOVIEMBRE DE 1988")
    elif tipo == "comisario":
        monigote(d, cx - 150 * s, piso + 10 * s, 0.9 * s, "policia", susto=True)
        cx2, cy2 = cx + 250 * s, piso - 330 * s
        for a in range(0, 360, 36):
            d.line([(cx2, cy2), (cx2 + math.cos(math.radians(a)) * 80 * s, cy2 + math.sin(math.radians(a)) * 80 * s)], fill=AMAR, width=7)
        etiqueta(d, cx, H * LABEL_Y, "COMISARIO CARLOS ZUNINO")
    elif tipo == "sereno":
        monigote(d, cx, piso + 10 * s, 0.9 * s, "sereno", brazos="frente", susto=True)
        d.rectangle([cx + 105 * s, piso - 230 * s, cx + 145 * s, piso - 180 * s], fill=AMAR, outline=OUT, width=3)
        etiqueta(d, cx, H * LABEL_Y, "EL SERENO DEL CEMENTERIO")
    elif tipo == "llaves":
        for k, dx in enumerate((-120, 60)):
            x0 = cx + dx * s
            d.ellipse([x0 - 50 * s, piso - 330 * s, x0 + 50 * s, piso - 230 * s], outline=AMAR, width=int(16 * s))
            d.rectangle([x0 - 10 * s, piso - 240 * s, x0 + 10 * s, piso - 60 * s], fill=AMAR)
            d.rectangle([x0, piso - 110 * s, x0 + 45 * s, piso - 90 * s], fill=AMAR)
        etiqueta(d, cx, H * LABEL_Y, "1994 · APARECEN LAS LLAVES")
    elif tipo == "expedientes":
        rnd = random.Random(9)
        for k in range(7):
            x0, y0 = cx + rnd.randint(-380, 300) * s, piso - rnd.randint(150, 520) * s
            d.rectangle([x0, y0, x0 + 170 * s, y0 + 120 * s], fill=(230, 200, 120), outline=OUT, width=4)
            d.text((x0 + 85 * s, y0 + 60 * s), "CAUSA", font=F(BEBAS, int(34 * s)), fill=OUT, anchor="mm")
        etiqueta(d, cx, H * LABEL_Y, "2008 · ROBAN EXPEDIENTES")
    elif tipo == "suiza":
        d.rectangle([cx - 230 * s, piso - 500 * s, cx + 230 * s, piso - 40 * s], fill=(120, 125, 135), outline=OUT, width=6)
        d.ellipse([cx - 120 * s, piso - 390 * s, cx + 120 * s, piso - 150 * s], fill=(90, 95, 105), outline=OUT, width=6)
        d.rectangle([cx - 80 * s, piso - 600 * s, cx + 80 * s, piso - 520 * s], fill=ROJO, outline=OUT, width=3)
        d.rectangle([cx - 12 * s, piso - 590 * s, cx + 12 * s, piso - 530 * s], fill="white")
        d.rectangle([cx - 35 * s, piso - 572 * s, cx + 35 * s, piso - 548 * s], fill="white")
        mano(d, cx, piso - 260 * s, 1.0 * s)
        etiqueta(d, cx, H * LABEL_Y, "¿UNA CUENTA EN SUIZA?")
    elif tipo == "logia":
        for dx in (-280, 0, 280):
            monigote(d, cx + dx * s, piso + 10 * s, 0.8 * s, "encapuchado")
        etiqueta(d, cx, H * LABEL_Y, "LOGIA P2")
    elif tipo == "adn":
        for k in range(24):
            y0 = piso - 560 * s + k * 22 * s
            a = k * 0.5
            x1, x2 = cx + math.sin(a) * 130 * s, cx - math.sin(a) * 130 * s
            d.line([(x1, y0), (x2, y0)], fill=(150, 150, 170), width=3)
            d.ellipse([x1 - 10 * s, y0 - 10 * s, x1 + 10 * s, y0 + 10 * s], fill=ROJO)
            d.ellipse([x2 - 10 * s, y0 - 10 * s, x2 + 10 * s, y0 + 10 * s], fill=(80, 140, 230))
        etiqueta(d, cx, H * LABEL_Y, "2006 · ADN: NEGATIVO")
    elif tipo == "traslado":
        d.rectangle([cx - 250 * s, piso - 280 * s, cx + 250 * s, piso], fill=(130, 130, 138), outline=OUT, width=5)
        d.polygon([(cx - 280 * s, piso - 280 * s), (cx, piso - 400 * s), (cx + 280 * s, piso - 280 * s)], fill=(105, 105, 112), outline=OUT)
        for dx in (-380, 380):
            for a in range(0, 360, 45):
                d.line([(cx + dx * s, piso - 420 * s), (cx + dx * s + math.cos(math.radians(a)) * 50 * s, piso - 420 * s + math.sin(math.radians(a)) * 50 * s)], fill=AMAR, width=5)
        etiqueta(d, cx, H * LABEL_Y, "SAN VICENTE · 2006")
    elif tipo == "comenta":
        monigote(d, cx, piso + 10 * s, 0.95 * s, "peron", brazos="uno", boca="sonrisa")
        etiqueta(d, cx, H * 0.09, "COMENTA \"PARTE 2\"", size=int(80 * s), fg=BLANCO)
    elif tipo == "encuesta":
        ops = [("1", "ROBO DEL LOUVRE", ROJO), ("2", "EL CUERPO DE EVITA", (40, 90, 200)), ("3", "DIAMANTES Y SÁNDWICH", (200, 140, 20))]
        etiqueta(d, cx, H * LABEL_Y, "¿QUÉ CASO SIGUE?", size=int(70 * s), bg=NEGRO)
        for i, (n, t, col) in enumerate(ops):
            y0 = (190 + i * 150) * s
            f = F(ANTON, int(64 * s))
            d.rounded_rectangle([cx - 420 * s, y0, cx + 420 * s, y0 + 115 * s], radius=int(20 * s), fill=col, outline=OUT, width=5)
            d.text((cx, y0 + 57 * s), f"{n} = {t}", font=f, fill=BLANCO, anchor="mm")
        monigote(d, cx, piso + 60 * s, 0.55 * s, "peron", brazos="duda", boca="sonrisa")
    elif tipo == "suscribete":
        monigote(d, cx, piso + 10 * s, 0.95 * s, "peron", brazos="uno", boca="sonrisa")
        etiqueta(d, cx, H * 0.09, "SUSCRÍBETE", size=int(90 * s))
    elif tipo == "pregunta":
        monigote(d, cx, piso + 10 * s, 0.95 * s, "peron", brazos="duda", boca="o")
        signo(d, cx - 220 * s, piso - 420 * s, int(150 * s)); signo(d, cx + 220 * s, piso - 420 * s, int(150 * s))
    else:  # peron
        monigote(d, cx, piso + 10 * s, 0.95 * s, "peron")
        etiqueta(d, cx, H * LABEL_Y, "JUAN DOMINGO PERÓN")
    return post(img)


REGLAS = [  # (palabras clave, escena) — se evalúan en orden
    (["uno, el robo", "tú eliges"], "encuesta"), (["suscríbete"], "suscribete"),
    (["comenta \"parte", "parte uno"], "comenta"), (["comentarios"], "pregunta"),
    (["faltan las manos", "cortaron las manos", "cortaría", "se las cortó", "se lleva tus manos", "manos ya no", "sierra", "cortan las dos", "le cortaron", "te las cortó", "cortarías", "cortadas", "cortó las dos"], "corte"),
    (["lobos", "naces"], "pueblo"), (["isla"], "isla"),
    (["evita", "eva duarte", "cuerpo de evita"], "evita"), (["italia", "escond", "desaparece", "dieciséis años"], "evita_oculta"),
    (["multitud", "plaza", "trabajadores", "obreros", "millones de personas", "gritan"], "multitud"),
    (["ejército", "militares", "derechos", "vacaciones", "aguinaldo", "tribunales"], "ejercito"),
    (["exilio", "paraguay", "huyes", "dieciocho años"], "exilio"),
    (["presidente", "elecciones", "intocable", "ganas"], "presidente"),
    (["vidrio", "blindado"], "vidrio"),
    (["mueres", "corazón", "setenta y ocho", "lloran"], "muerte"),
    (["sable"], "sable"), (["suiza", "huellas", "caja de seguridad"], "suiza"),
    (["logia", "gelli", "p2", "periodistas"], "logia"), (["adn", "hija", "muestras", "negativo"], "adn"),
    (["san vicente", "tiros", "traslad", "último viaje"], "traslado"),
    (["expedientes", "papeles del robo"], "expedientes"), (["llaves"], "llaves"),
    (["juez"], "juez"), (["accidente", "choque", "peritaje"], "choque"),
    (["comisario", "disparo", "zunino", "baleado"], "comisario"), (["sereno", "lavagno", "asesinado", "muerto cerca"], "sereno"),
    (["trozo", "papel", "isabel"], "papel"), (["carta", "hermes", "dólares", "rescate", "dinero", "broma"], "cartas"),
    (["vidrio", "blindado"], "vidrio"), (["no se lleva tu cuerpo", "entra a tu bóveda", "herramientas", "agujero", "nadie los vea", "atraviesa"], "ladron"),
    (["una noche", "junio de mil", "sin que nadie"], "cementerio"),
    (["ataúd", "manos", "bóveda", "chacarita", "cementerio"], "ataud"), (["?"], "pregunta"), (["perón"], "peron"),
]


def elegir(texto, anterior):
    t = texto.lower()
    for claves, esc in REGLAS:
        if any(c in t for c in claves):
            return esc
    return anterior or "peron"


# ---------------------------------------------------------------- subtítulos
def bloques(frases):
    """Divide cada frase en bloques de máx 3 palabras con tiempo por palabra."""
    out = []
    for f in frases:
        pal = f["texto"].split()
        pesos = [len(p) + 2 for p in pal]
        tot = sum(pesos); dur = f["fin"] - f["ini"]; t = f["ini"]
        tiempos = []
        for p, w in zip(pal, pesos):
            tiempos.append((p, t, t + dur * w / tot)); t += dur * w / tot
        for i in range(0, len(tiempos), 3):
            g = tiempos[i:i + 3]
            out.append({"palabras": g, "ini": g[0][1], "fin": g[-1][2]})
    return out


def dibujar_sub(img, bloque, t, area, size):
    d = ImageDraw.Draw(img)
    f = F(ANTON, size)
    pal = [p.upper().strip('"') for p, _, _ in bloque["palabras"]]
    activa = max([i for i, (_, a, _) in enumerate(bloque["palabras"]) if a <= t] or [0])
    total = sum(d.textlength(p + " ", font=f) for p in pal)
    x0, y0, x1, y1 = area
    x = (x0 + x1 - total) / 2; y = (y0 + y1) / 2
    for i, p in enumerate(pal):
        col = ROJO if i == activa else BLANCO
        d.text((x + 4, y + 6), p, font=f, fill=(0, 0, 0), anchor="lm")
        d.text((x, y), p, font=f, fill=col, stroke_width=5, stroke_fill=NEGRO, anchor="lm")
        x += d.textlength(p + " ", font=f)


IMPACTO = {"corte", "choque", "comisario", "ladron", "sable", "traslado", "cartas"}
FLASH = {"comisario", "choque", "traslado"}


def sfx(cambios, impactos, dur, ruta, sr=44100):
    """Efectos sintetizados: whoosh en cada cambio de escena y golpe grave en los impactos."""
    import numpy as np, wave
    out = np.zeros(int((dur + 1) * sr), dtype=np.float32)
    rng = np.random.default_rng(1)
    def put(t, x):
        i = int(t * sr); j = min(len(out), i + len(x)); out[i:j] += x[: j - i]
    n = int(0.45 * sr); tt = np.linspace(0, 1, n)
    ruido = rng.standard_normal(n).astype(np.float32)
    # whoosh: ruido filtrado con barrido (media móvil decreciente) y envolvente
    k = 24; ruido_f = np.convolve(ruido, np.ones(k) / k, mode="same")
    whoosh = ruido_f * np.sin(np.pi * tt) ** 2 * 0.22
    m = int(0.9 * sr); tb = np.arange(m) / sr
    boom = (np.sin(2 * np.pi * (48 + 30 * np.exp(-tb * 8)) * tb) * np.exp(-tb * 4.5) * 0.55
            + np.convolve(rng.standard_normal(m), np.ones(60) / 60, mode="same") * np.exp(-tb * 14) * 0.5).astype(np.float32)
    for t in cambios:
        put(max(0, t - 0.2), whoosh)
    for t in impactos:
        put(t, boom)
    out = np.clip(out, -1, 1)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    import numpy as np
    src, salida, orient, final = sys.argv[1:5]
    titulo = os.environ.get("TITULO", "PERÓN")
    data = json.load(open(os.path.join(src, "tiempos.json")))
    frases = data["frases"]; dur = data["duracion"] + 1.5
    V = orient == "vertical"
    W, H = (1080, 1920) if V else (1920, 1080)
    if V:
        zona = (0, 375, W, 1475); sub = (0, 1475, W, 1720); sub_size = 104
    else:
        zona = (0, 0, W, H); sub = (0, 900, W, 1040); sub_size = 86
    zw, zh = zona[2] - zona[0], zona[3] - zona[1]
    global LABEL_Y
    LABEL_Y = 0.115 if V else 0.19
    esc_prev, escenas = None, []
    for f in frases:
        e = elegir(f["texto"], esc_prev); escenas.append(e); esc_prev = e
    if final == "parte1":
        escenas[-1] = "comenta"
    elif final == "encuesta":
        ini = max(i for i, f in enumerate(frases) if "tú eliges" in f["texto"].lower())
        for i in range(ini, len(frases)):
            escenas[i] = "encuesta"
    elif final == "suscribete":
        for i in range(len(frases) - 2, len(frases)):
            if "suscríbete" in frases[i]["texto"].lower():
                escenas[i] = "suscribete"
    cache = {}
    def img_escena(e):
        if e not in cache:
            cache[e] = escena(e, int(zw * 1.12), int(zh * 1.12))
        return cache[e]
    blq = bloques(frases)
    cambios = [f["ini"] for i, f in enumerate(frases) if i and escenas[i] != escenas[i - 1]]
    impactos = [f["ini"] for i, f in enumerate(frases) if escenas[i] in IMPACTO and (i == 0 or escenas[i] != escenas[i - 1])]
    ruta_sfx = os.path.join(src, "sfx.wav")
    sfx(cambios, impactos, dur, ruta_sfx)
    # capa fija: cabecera, líneas rojas, zona de subtítulos con degradado rojo
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(capa)
    if V:
        hd.rectangle([0, 0, W, zona[1]], fill=(8, 8, 10, 255))
        ft = F(ANTON, 128)
        txt = " ".join(titulo)
        hd.text((W / 2 + 4, 170 + 5), txt, font=ft, fill=(0, 0, 0, 255), anchor="mm")
        hd.text((W / 2, 170), txt, font=ft, fill=BLANCO, anchor="mm")
        fe = F(ELITE, 40); tag = "CASOS QUE NADIE NOTÓ"; tw = hd.textlength(tag, font=fe)
        hd.rectangle([W / 2 - tw / 2 - 22, 262, W / 2 + tw / 2 + 22, 318], fill=ROJO)
        hd.text((W / 2, 290), tag, font=fe, fill=BLANCO, anchor="mm")
        for y in range(zona[3], H):
            t = (y - zona[3]) / (H - zona[3])
            hd.line([(0, y), (W, y)], fill=(int(10 + 60 * t), int(6 + 6 * t), int(8 + 6 * t), 255))
        for y in (zona[1], zona[3]):
            hd.line([(0, y), (W, y)], fill=ROJO, width=5)
        hd.text((W / 2, 1780), "  ".join("SÍGUEME PARA MÁS CASOS"), font=F(ELITE, 30), fill=(170, 170, 170, 255), anchor="mm")
    else:
        for y in range(780, H):
            t = (y - 780) / (H - 780)
            hd.line([(0, y), (W, y)], fill=(0, 0, 0, int(215 * t)))
        hd.rectangle([0, 0, 720, 150], fill=(8, 8, 10, 225))
        hd.line([(0, 150), (720, 150)], fill=ROJO, width=4)
        hd.text((40, 62), " ".join(titulo), font=F(ANTON, 76), fill=BLANCO, anchor="lm")
        fe = F(ELITE, 28); tag = "CASOS QUE NADIE NOTÓ"; tw = hd.textlength(tag, font=fe)
        hd.rectangle([36, 104, 36 + tw + 28, 140], fill=ROJO)
        hd.text((50, 122), tag, font=fe, fill=BLANCO, anchor="lm")
    # grano animado
    rng = np.random.default_rng(4)
    granos = []
    for _ in range(6):
        g = rng.normal(0, 12, (zh // 2, zw // 2)).astype(np.int16)
        granos.append(np.repeat(np.repeat(g, 2, 0), 2, 1)[:zh, :zw, None])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", os.path.join(src, "voz.wav"), "-i", ruta_sfx,
           "-filter_complex", f"anoisesrc=c=brown:a=0.02:d={dur},lowpass=f=180,volume=0.5[n];"
                              f"sine=f=55:d={dur},volume=0.025[s1];[n][s1]amix=2:normalize=0,afade=t=in:d=2[bg];"
                              "[1:a]apad[v];[2:a]volume=0.9[fx];[v][bg][fx]amix=3:normalize=0:duration=shortest[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.2f}", "-movflags", "+faststart", salida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(dur * FPS); fi = 0; bi = 0
    shake_rng = random.Random(7)
    for k in range(n):
        t = k / FPS
        while fi + 1 < len(frases) and t >= frases[fi + 1]["ini"]:
            fi += 1
        f = frases[fi]
        nueva = escenas[fi] != (escenas[fi - 1] if fi else None)
        dt = t - f["ini"]
        prog = min(1, max(0, dt / max(0.5, f["fin"] - f["ini"] + 0.4)))
        punch = max(0, 1 - dt * 5) * 0.07 if nueva else 0
        z = 1.0 + 0.05 * prog + punch
        src_img = img_escena(escenas[fi])
        sw, sh = src_img.size
        cw, ch = sw / (1.12 * z), sh / (1.12 * z)
        # deriva lenta de cámara y temblor en impactos
        ox = (sw - cw) / 2 + math.sin(t * 0.35) * sw * 0.01
        oy = (sh - ch) / 2 + math.cos(t * 0.27) * sh * 0.008
        if nueva and escenas[fi] in IMPACTO and dt < 0.45:
            amp = (0.45 - dt) * 60
            ox += shake_rng.uniform(-amp, amp); oy += shake_rng.uniform(-amp, amp)
        ox = min(max(0, ox), sw - cw); oy = min(max(0, oy), sh - ch)
        view = np.asarray(src_img.resize((zw, zh), Image.BILINEAR, box=(ox, oy, ox + cw, oy + ch)), dtype=np.int16)
        view = view + granos[(k // 2) % len(granos)]
        flick = 1.0 + 0.035 * math.sin(t * 9.1) * math.sin(t * 3.7)  # parpadeo de luz
        view = view * flick
        if nueva and escenas[fi] in FLASH and dt < 0.25:
            view = view + (0.25 - dt) / 0.25 * 170
        if dt < 0.12 and nueva:  # fundido rápido desde negro
            view = view * (0.35 + dt / 0.12 * 0.65)
        frame = Image.new("RGB", (W, H), NEGRO)
        frame.paste(Image.fromarray(np.clip(view, 0, 255).astype(np.uint8)), (zona[0], zona[1]))
        frame.paste(capa, (0, 0), capa)
        while bi + 1 < len(blq) and t >= blq[bi + 1]["ini"]:
            bi += 1
        if blq[bi]["ini"] - 0.05 <= t <= blq[bi]["fin"] + 0.35:
            dibujar_sub(frame, blq[bi], t, sub, sub_size)
        p.stdin.write(frame.tobytes())
        if k % (FPS * 60) == 0:
            print(f"{t:6.0f}s / {dur:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("listo", salida)


if __name__ == "__main__":
    main()
