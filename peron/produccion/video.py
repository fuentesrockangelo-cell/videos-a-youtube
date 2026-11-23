"""Arma el video con monigotes, cabecera y subtítulos karaoke.

Uso: python3 video.py <dir_con_voz_y_tiempos> <salida.mp4> <vertical|horizontal> <final: parte1|encuesta|suscribete>
Fuentes: variable FONTS_DIR con fontsource-anton.woff y fontsource-bebas-neue.woff
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = os.environ["FONTS_DIR"]
ANTON = os.path.join(FD, "fontsource-anton.woff")
BEBAS = os.path.join(FD, "fontsource-bebas-neue.woff")
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


def monigote(d, x, y, s=1.0, tipo="peron", brazos="abajo", boca="normal", susto=False):
    """x,y = pies (centro). Altura total ~ 480*s."""
    s *= 1.45
    w = int(4 * s)
    trajes = {"peron": (70, 85, 60), "peron_viejo": (40, 40, 48), "soldado": (85, 95, 60),
              "obrero": (60, 90, 140), "evita": (230, 230, 225), "juez": (25, 25, 28),
              "policia": (35, 60, 130), "sereno": (110, 85, 55), "ladron": (25, 25, 28),
              "encapuchado": (60, 20, 25), "mujer": (150, 60, 90)}
    c = trajes.get(tipo, (70, 70, 70))
    # piernas
    for dx in (-22, 22):
        d.rectangle([x + (dx - 10) * s, y - 95 * s, x + (dx + 10) * s, y], fill=OUT)
        d.ellipse([x + (dx - 16) * s, y - 12 * s, x + (dx + 18) * s, y + 6 * s], fill=OUT)
    # cuerpo
    if tipo in ("evita", "mujer"):
        d.polygon([(x - 40 * s, y - 210 * s), (x + 40 * s, y - 210 * s), (x + 70 * s, y - 80 * s), (x - 70 * s, y - 80 * s)],
                  fill=c, outline=OUT, width=w)
    elif tipo in ("juez", "encapuchado"):
        d.polygon([(x - 50 * s, y - 210 * s), (x + 50 * s, y - 210 * s), (x + 65 * s, y - 40 * s), (x - 65 * s, y - 40 * s)],
                  fill=c, outline=OUT, width=w)
    else:
        d.rounded_rectangle([x - 50 * s, y - 215 * s, x + 50 * s, y - 85 * s], radius=int(18 * s), fill=c, outline=OUT, width=w)
        if tipo in ("peron", "soldado", "policia", "peron_viejo"):
            for i in range(3):
                d.ellipse([x - 5 * s, y - (190 - i * 35) * s, x + 5 * s, y - (180 - i * 35) * s], fill=AMAR)
        if tipo == "peron":  # banda presidencial
            d.polygon([(x - 50 * s, y - 210 * s), (x - 30 * s, y - 215 * s), (x + 50 * s, y - 110 * s), (x + 50 * s, y - 90 * s)],
                      fill=(117, 170, 219))
            d.line([(x - 40 * s, y - 212 * s), (x + 50 * s, y - 100 * s)], fill="white", width=int(6 * s))
    # brazos
    hx = {"abajo": [(-75, -110), (75, -110)], "arriba": [(-80, -300), (80, -300)], "uno": [(-75, -110), (85, -300)],
          "frente": [(-75, -110), (120, -190)], "duda": [(-95, -230), (95, -230)]}[brazos]
    for (dx, dy), sgn in zip(hx, (-1, 1)):
        d.line([(x + sgn * 45 * s, y - 200 * s), (x + dx * s, y + dy * s)], fill=c if tipo != "evita" else PIEL, width=int(18 * s))
        d.ellipse([x + dx * s - 11 * s, y + dy * s - 11 * s, x + dx * s + 11 * s, y + dy * s + 11 * s], fill=PIEL, outline=OUT, width=int(3 * s))
    # cabeza
    hy = y - 265 * s
    r = 55 * s
    if tipo == "evita":
        d.ellipse([x - 30 * s, hy - 95 * s, x + 30 * s, hy - 40 * s], fill=(240, 200, 80), outline=OUT, width=w)  # moño
    d.ellipse([x - r, hy - r, x + r, hy + r], fill=PIEL, outline=OUT, width=w)
    pelo = {"peron": (25, 25, 25), "peron_viejo": (170, 170, 170), "evita": (240, 200, 80), "juez": (220, 220, 220),
            "mujer": (60, 35, 25)}.get(tipo, (40, 30, 25))
    if tipo in ("ladron", "encapuchado"):
        d.ellipse([x - r - 4 * s, hy - r - 4 * s, x + r + 4 * s, hy + r + 4 * s], fill=c if tipo == "encapuchado" else (25, 25, 28), outline=OUT, width=w)
        if tipo == "encapuchado":
            d.polygon([(x - r, hy - 20 * s), (x, hy - r - 60 * s), (x + r, hy - 20 * s)], fill=c, outline=OUT)
        d.rectangle([x - 40 * s, hy - 22 * s, x + 40 * s, hy + 12 * s], fill=PIEL)
        ojos(d, x, hy - 5 * s, s * 0.85, susto=susto)
        return
    d.chord([x - r, hy - r, x + r, hy + r], 180, 360, fill=pelo, outline=OUT, width=w)
    if tipo in ("peron", "soldado", "policia", "peron_viejo"):  # gorra militar
        gc = (55, 70, 45) if tipo != "policia" else (25, 40, 100)
        d.rounded_rectangle([x - 52 * s, hy - 85 * s, x + 52 * s, hy - 35 * s], radius=int(12 * s), fill=gc, outline=OUT, width=w)
        d.rectangle([x - 55 * s, hy - 42 * s, x + 55 * s, hy - 30 * s], fill=OUT)
        d.ellipse([x - 9 * s, hy - 72 * s, x + 9 * s, hy - 54 * s], fill=AMAR)
    if tipo == "obrero":
        d.chord([x - 55 * s, hy - 75 * s, x + 55 * s, hy - 5 * s], 180, 360, fill=(60, 90, 140), outline=OUT, width=w)
    if tipo == "sereno":
        d.rounded_rectangle([x - 50 * s, hy - 75 * s, x + 50 * s, hy - 35 * s], radius=int(10 * s), fill=(80, 60, 40), outline=OUT, width=w)
    ojos(d, x, hy - 5 * s, s, susto=susto)
    if boca == "sonrisa":
        d.arc([x - 25 * s, hy + 5 * s, x + 25 * s, hy + 35 * s], 10, 170, fill=OUT, width=int(4 * s))
    elif boca == "o" or susto:
        d.ellipse([x - 9 * s, hy + 18 * s, x + 9 * s, hy + 38 * s], fill=OUT)
    else:
        d.line([(x - 15 * s, hy + 27 * s), (x + 15 * s, hy + 27 * s)], fill=OUT, width=int(4 * s))
    if tipo == "peron_viejo":
        d.line([(x - 30 * s, hy - 25 * s), (x - 8 * s, hy - 20 * s)], fill=OUT, width=int(3 * s))
        d.line([(x + 30 * s, hy - 25 * s), (x + 8 * s, hy - 20 * s)], fill=OUT, width=int(3 * s))


# ---------------------------------------------------------------- fondos
def fondo(img, tipo):
    W, H = img.size
    d = ImageDraw.Draw(img)
    piso = int(H * 0.82)
    if tipo == "noche":
        for i in range(H):
            t = i / H
            d.line([(0, i), (W, i)], fill=(int(15 + 15 * t), int(18 + 20 * t), int(45 + 30 * t)))
        rnd = random.Random(3)
        for _ in range(70):
            x, y = rnd.randrange(W), rnd.randrange(int(H * 0.6))
            d.ellipse([x, y, x + 3, y + 3], fill=(230, 230, 240))
        d.ellipse([W * 0.78, H * 0.07, W * 0.78 + 90, H * 0.07 + 90], fill=(235, 230, 190))
        d.rectangle([0, piso, W, H], fill=(55, 60, 55))
    elif tipo == "cripta":
        d.rectangle([0, 0, W, H], fill=(70, 66, 62))
        for yy in range(0, piso, 60):
            off = 0 if (yy // 60) % 2 else 60
            for xx in range(-off, W, 120):
                d.rectangle([xx, yy, xx + 118, yy + 58], outline=(50, 47, 44), width=3)
        d.rectangle([0, piso, W, H], fill=(40, 38, 36))
    elif tipo == "plaza":
        for i in range(H):
            t = i / H
            d.line([(0, i), (W, i)], fill=(int(120 + 60 * t), int(170 + 40 * t), 230))
        bx = W // 2
        d.rectangle([bx - 300, piso - 330, bx + 300, piso], fill=(226, 160, 160), outline=OUT, width=4)  # Casa Rosada
        for i in range(-250, 260, 100):
            d.rectangle([bx + i - 25, piso - 280, bx + i + 25, piso - 200], fill=(70, 90, 120), outline=OUT, width=3)
        d.rectangle([0, piso, W, H], fill=(150, 150, 140))
    elif tipo == "oficina":
        d.rectangle([0, 0, W, H], fill=(140, 95, 60))
        for xx in range(0, W, 40):
            d.line([(xx, 0), (xx, piso)], fill=(125, 84, 52), width=2)
        d.rectangle([0, piso, W, H], fill=(70, 45, 30))
    elif tipo == "isla":
        for i in range(H):
            t = i / H
            d.line([(0, i), (W, i)], fill=(int(90 + 50 * t), int(110 + 50 * t), int(150 + 40 * t)))
        d.rectangle([0, int(H * 0.6), W, H], fill=(40, 80, 130))
        for k in range(8):
            yy = int(H * 0.65) + k * 40
            d.arc([-50 + (k % 2) * 60, yy, W, yy + 30], 0, 180, fill=(120, 170, 220), width=3)
    else:  # oscuro con viñeta roja
        d.rectangle([0, 0, W, H], fill=NEGRO)
        glow = Image.new("RGB", (W, H), NEGRO)
        gd = ImageDraw.Draw(glow)
        gd.ellipse([W * 0.2, H * 0.15, W * 0.8, H * 0.85], fill=(120, 15, 20))
        glow = glow.filter(ImageFilter.GaussianBlur(min(W, H) // 6))
        img.paste(glow)
    return piso


def etiqueta(d, x, y, txt, size=58, fg=BLANCO, bg=ROJO):
    f = F(BEBAS, size)
    w = d.textlength(txt, font=f)
    d.rectangle([x - w / 2 - 16, y - 6, x + w / 2 + 16, y + size + 4], fill=bg, outline=OUT, width=3)
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
        monigote(d, cx + 330 * s, piso + 10 * s, 0.8 * s, "ladron", brazos="frente")
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
        d.rectangle([cx - 250 * s, piso - 280 * s, cx + 250 * s, piso], fill=(200, 200, 205), outline=OUT, width=5)
        d.polygon([(cx - 280 * s, piso - 280 * s), (cx, piso - 400 * s), (cx + 280 * s, piso - 280 * s)], fill=(180, 180, 185), outline=OUT)
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
    return img


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
        d.text((x, y), p, font=f, fill=col, stroke_width=6, stroke_fill=NEGRO, anchor="lm")
        x += d.textlength(p + " ", font=f)


def main():
    src, salida, orient, final = sys.argv[1:5]
    data = json.load(open(os.path.join(src, "tiempos.json")))
    frases = data["frases"]; dur = data["duracion"] + 1.5
    W, H = (1080, 1920) if orient == "vertical" else (1920, 1080)
    if orient == "vertical":
        cab = (0, 0, W, 300); zona = (0, 300, W, 1500); sub = (0, 1500, W, 1800); sub_size = 96
    else:
        cab = (0, 0, W, 150); zona = (0, 0, W, H); sub = (0, 880, W, 1040); sub_size = 84
    zw, zh = zona[2] - zona[0], zona[3] - zona[1]
    global LABEL_Y
    if orient != "vertical":
        LABEL_Y = 0.17
    # escenas por frase
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
    # cabecera fija
    head = Image.new("RGBA", (W, cab[3]), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    if orient == "vertical":
        hd.rectangle([0, 0, W, cab[3]], fill=NEGRO)
        hd.text((W / 2, 120), "LAS MANOS DE PERÓN", font=F(ANTON, 110), fill=BLANCO, anchor="mm")
        etiqueta(hd, W / 2, 205, "CASOS QUE NADIE NOTÓ", size=44)
        hd.line([(0, cab[3] - 4), (W, cab[3] - 4)], fill=ROJO, width=6)
    else:
        hd.rectangle([0, 0, 760, 130], fill=(12, 12, 14, 210))
        hd.text((30, 50), "LAS MANOS DE PERÓN", font=F(ANTON, 64), fill=BLANCO, anchor="lm")
        etiqueta(hd, 210, 88, "CASOS QUE NADIE NOTÓ", size=30)
    pie = F(BEBAS, 34)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", os.path.join(src, "voz.wav"),
           "-filter_complex", f"anoisesrc=c=brown:a=0.02:d={dur},lowpass=f=180,volume=0.5[n];"
                              f"sine=f=55:d={dur},volume=0.025[s1];[n][s1]amix=2:normalize=0,afade=t=in:d=2[bg];"
                              "[1:a]apad[v];[v][bg]amix=2:normalize=0:duration=shortest[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.2f}", "-movflags", "+faststart", salida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(dur * FPS); fi = 0; bi = 0
    for k in range(n):
        t = k / FPS
        while fi + 1 < len(frases) and t >= frases[fi + 1]["ini"]:
            fi += 1
        f = frases[fi]
        prog = min(1, max(0, (t - f["ini"]) / max(0.5, f["fin"] - f["ini"] + 0.4)))
        punch = max(0, 1 - (t - f["ini"]) * 6) * 0.05 if escenas[fi] != (escenas[fi - 1] if fi else None) else 0
        z = 1.0 + 0.04 * prog + punch
        src_img = img_escena(escenas[fi])
        cw, ch = src_img.size[0] / (1.12 * z) * 1.0, src_img.size[1] / (1.12 * z)
        ox, oy = (src_img.size[0] - cw) / 2, (src_img.size[1] - ch) / 2
        frame = Image.new("RGB", (W, H), NEGRO)
        frame.paste(src_img.resize((zw, zh), Image.BILINEAR, box=(ox, oy, ox + cw, oy + ch)), (zona[0], zona[1]))
        frame.paste(head, (0, 0), head)
        d = ImageDraw.Draw(frame)
        if orient == "vertical":
            d.rectangle([sub[0], sub[1], W, H], fill=(20, 6, 8))
            d.text((W / 2, 1860), "S Í G U E M E   P A R A   M Á S   C A S O S", font=pie, fill=(150, 150, 150), anchor="mm")
        if orient != "vertical":
            band = Image.new("RGBA", (W, 170), (0, 0, 0, 140))
            frame.paste(band, (0, 875), band)
        while bi + 1 < len(blq) and t >= blq[bi + 1]["ini"]:
            bi += 1
        if blq[bi]["ini"] - 0.05 <= t <= blq[bi]["fin"] + 0.35:
            dibujar_sub(frame, blq[bi], t, sub, sub_size)
        # barra de progreso arriba
        d.rectangle([0, 0, int(W * t / dur), 8], fill=ROJO)
        p.stdin.write(frame.tobytes())
        if k % (FPS * 30) == 0:
            print(f"{t:6.0f}s / {dur:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("listo", salida)


if __name__ == "__main__":
    main()
