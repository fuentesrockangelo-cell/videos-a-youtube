"""Video en estilo "expediente": cada persona o pista del caso es una ficha animada.

Uso: FONTS_DIR=... python3 ficha.py <dir_voz> <salida.mp4> <vertical|horizontal> <final: parte1|encuesta|suscribete>
"""
import math, os, random, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

os.environ.pop("PERSONAJES", None)
import video as V

F = V.F; ANTON = V.ANTON; BEBAS = V.BEBAS; ELITE = V.ELITE
FPS = 25
FONDO = (14, 9, 20)
TARJ = (24, 16, 32)
MORADO = (150, 80, 230)
MORADO_OSC = (70, 40, 110)
BLANCO = (240, 236, 245)
GRIS = (150, 140, 165)
ROJO = (225, 40, 50)

FICHAS = {
    "peron": dict(titulo="JUAN DOMINGO PERÓN", peligro=3, sello="3 VECES PRESIDENTE",
                  campos=[("NACIÓ", "LOBOS, 1895"), ("MURIÓ", "1 DE JULIO DE 1974")],
                  stats=[("PODER", 5), ("FAMA", 5), ("ENEMIGOS", 4), ("MISTERIO", 3)], evidencia="SUS MANOS"),
    "evita": dict(titulo="EVA DUARTE · EVITA", peligro=2, sello="ESCONDIDA 16 AÑOS",
                  campos=[("PAPEL", "PRIMERA DAMA"), ("MURIÓ", "1952 · 33 AÑOS")],
                  stats=[("CARISMA", 5), ("FAMA", 5), ("ENEMIGOS", 4), ("MISTERIO", 4)], evidencia="CUERPO EN ITALIA"),
    "tumba": dict(titulo="LA BÓVEDA", peligro=3, sello="IMPENETRABLE",
                  campos=[("LUGAR", "CHACARITA, BUENOS AIRES"), ("PROTECCIÓN", "VIDRIO BLINDADO 8 CM")],
                  stats=[("SEGURIDAD", 4), ("VIGILANCIA", 2), ("ACCESO", 1), ("MISTERIO", 4)], evidencia="LLAVES DEL GOBIERNO"),
    "ladron": dict(titulo="LOS PROFANADORES", peligro=5, sello="SIN IDENTIFICAR",
                   campos=[("CUÁNDO", "JUNIO DE 1987"), ("CON QUÉ", "UNA SIERRA")],
                   stats=[("SIGILO", 5), ("RAPIDEZ", 4), ("PELIGRO", 5), ("MISTERIO", 5)], evidencia="MANOS Y SABLE"),
    "cartas": dict(titulo="HERMES IAI Y LOS 13", peligro=4, sello="RESCATE",
                   campos=[("PIDEN", "8 MILLONES DE DÓLARES"), ("PRUEBA", "CARTA DE ISABEL")],
                   stats=[("AMENAZA", 4), ("SECRETO", 5), ("PRUEBAS", 3), ("MISTERIO", 5)], evidencia="3 CARTAS IDÉNTICAS"),
    "juez": dict(titulo="JUEZ JAIME FAR SUAU", peligro=4, sello="MUERTO",
                 campos=[("INVESTIGÓ", "LA BÓVEDA"), ("MURIÓ", "NOV. 1988 · CHOQUE")],
                 stats=[("PODER", 3), ("PISTAS", 3), ("RIESGO", 5), ("MISTERIO", 4)], evidencia="PERITAJE NUNCA HECHO"),
    "comisario": dict(titulo="COMISARIO CARLOS ZUNINO", peligro=3, sello="SOBREVIVIÓ",
                      campos=[("ATAQUE", "DISPARO EN LA CABEZA"), ("DÓNDE", "EN SU CASA")],
                      stats=[("PISTAS", 3), ("SUERTE", 5), ("RIESGO", 5), ("MISTERIO", 4)], evidencia="ATACANTES DESCONOCIDOS"),
    "sereno": dict(titulo="EL SERENO · PAULINO LAVAGNO", peligro=4, sello="ASESINADO",
                   campos=[("TRABAJO", "CEMENTERIO"), ("AVISÓ", "QUE LO QUERÍAN MATAR")],
                   stats=[("TESTIGO", 4), ("MIEDO", 5), ("RIESGO", 5), ("MISTERIO", 4)], evidencia="AUTOPSIA (SEGÚN PRENSA)"),
    "causa": dict(titulo="LA CAUSA JUDICIAL", peligro=3, sello="SIN CULPABLES",
                  campos=[("1994", "APARECEN LAS LLAVES"), ("2008", "ROBAN EXPEDIENTES")],
                  stats=[("AVANCES", 1), ("PISTAS", 3), ("CAOS", 5), ("MISTERIO", 5)], evidencia="LLAVES EN UNA COMISARÍA"),
    "suiza": dict(titulo="TEORÍA 1 · SUIZA", peligro=2, sello="SIN PRUEBAS",
                  campos=[("IDEA", "UNA CUENTA SECRETA"), ("LLAVE", "SUS MANOS")],
                  stats=[("PROBABILIDAD", 2), ("PRUEBAS", 1), ("RAREZA", 4), ("MISTERIO", 4)], evidencia="NUNCA SE PROBÓ"),
    "rescate": dict(titulo="TEORÍA 2 · RESCATE", peligro=2, sello="DUDOSA",
                    campos=[("IDEA", "COBRAR 8 MILLONES"), ("PROBLEMA", "NO HUBO MÁS CARTAS")],
                    stats=[("PROBABILIDAD", 2), ("PRUEBAS", 2), ("RAREZA", 2), ("MISTERIO", 3)], evidencia="CARTAS DE HERMES"),
    "logia": dict(titulo="TEORÍA 3 · LOGIA P2", peligro=5, sello="NEGADO",
                  campos=[("LÍDER", "LICIO GELLI"), ("ÉL DIJO", "QUE NO FUE ÉL")],
                  stats=[("PROBABILIDAD", 3), ("PRUEBAS", 1), ("RAREZA", 5), ("MISTERIO", 5)], evidencia="¿LA FRASE DE PERÓN?"),
    "adn": dict(titulo="2006 · LA TUMBA OTRA VEZ", peligro=3, sello="SIN PAZ",
                campos=[("ADN", "NEGATIVO"), ("TRASLADO", "SAN VICENTE · A TIROS")],
                stats=[("CAOS", 5), ("PRUEBAS", 2), ("RIESGO", 4), ("MISTERIO", 4)], evidencia="MUESTRAS DE SUS RESTOS"),
    "final": dict(titulo="CASO ABIERTO", peligro=5, sello="SIN RESOLVER",
                  campos=[("LAS MANOS", "NUNCA APARECIERON"), ("CONDENADOS", "NINGUNO")],
                  stats=[("PRUEBAS", 1), ("TEORÍAS", 5), ("MUERTES", 4), ("MISTERIO", 5)], evidencia="¿TÚ QUÉ CREES?"),
}

ESCENA_A_FICHA = {**{e: "peron" for e in ("pueblo", "ejercito", "isla", "multitud", "presidente", "peron", "muerte", "exilio")},
                  "evita": "evita", "evita_oculta": "evita", "ataud": "tumba", "vidrio": "tumba",
                  "cementerio": "ladron", "ladron": "ladron", "corte": "ladron", "sable": "ladron",
                  "cartas": "cartas", "papel": "cartas", "dinero": "cartas", "juez": "juez", "choque": "juez",
                  "comisario": "comisario", "sereno": "sereno", "llaves": "causa", "expedientes": "causa",
                  "suiza": "suiza", "logia": "logia", "adn": "adn", "traslado": "adn"}


def asignar_fichas(frases, escenas):
    out, actual, teoria, final = [], "tumba", None, False
    for f, e in zip(frases, escenas):
        t = f["texto"].lower()
        if "primera teoría" in t: teoria = "suiza"
        elif "segunda teoría" in t: teoria = "rescate"
        elif "tercera teoría" in t: teoria = "logia"
        if e in ("adn", "traslado"): teoria = None
        if "cuarenta años después" in t or "lo único seguro" in t or "nadie fue condenado" in t:
            final, teoria = True, None
        if e in ("comenta", "encuesta", "suscribete"):
            actual = e
        elif final:
            actual = "final"
        elif teoria:
            actual = teoria
        elif e in ESCENA_A_FICHA:
            actual = ESCENA_A_FICHA[e]
        out.append(actual)
    return out


# ---------------------------------------------------------------- dibujo
def calavera(d, x, y, r, lleno):
    col = MORADO if lleno else None
    d.ellipse([x - r, y - r, x + r, y + r * 0.85], fill=col, outline=MORADO, width=3)
    d.rectangle([x - r * 0.55, y + r * 0.6, x + r * 0.55, y + r * 1.05], fill=col, outline=MORADO, width=3)
    oj = FONDO if lleno else MORADO
    for dx in (-0.38, 0.38):
        d.ellipse([x + dx * r - r * 0.25, y - r * 0.15, x + dx * r + r * 0.25, y + r * 0.3], fill=oj)


def texto_ajustado(d, xy, txt, fuente, size, ancho, fill, anchor="la"):
    while size > 20 and d.textlength(txt, font=F(fuente, size)) > ancho:
        size -= 4
    d.text(xy, txt, font=F(fuente, size), fill=fill, anchor=anchor)
    return size


def neon_rect(base, box, col, w=4, glow=10, alpha=1.0):
    lay = Image.new("RGB", base.size, (0, 0, 0))
    ImageDraw.Draw(lay).rectangle(box, outline=tuple(int(c * alpha) for c in col), width=w + 4)
    base.paste(ImageChops.add(base, lay.filter(ImageFilter.GaussianBlur(glow))))
    ImageDraw.Draw(base).rectangle(box, outline=col, width=w)


def sello(base, cx, cy, txt, size, escala=1.0, ang=-8):
    f = F(ANTON, int(size * escala))
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    w = int(d0.textlength(txt, font=f)) + 60; h = int(size * escala * 1.55)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle([4, 4, w - 5, h - 5], outline=(200, 110, 255, 255), width=max(3, int(6 * escala)))
    d.text((w / 2, h / 2), txt, font=f, fill=(210, 140, 255, 255), anchor="mm")
    lay = lay.rotate(ang, expand=True, resample=Image.BICUBIC)
    g = lay.filter(ImageFilter.GaussianBlur(8))
    base.paste(g, (int(cx - lay.width / 2), int(cy - lay.height / 2)), g)
    base.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


def layout(V_):
    if V_:
        W, H = 1080, 1920
        return dict(W=W, H=H, card=(40, 60, W - 40, H - 60), top=100, titulo=(W / 2, 205), tsize=110, calav=(W / 2, 320),
                    ventana=(80, 380, W - 80, 1010), caption=(W / 2, 1085), csize=60,
                    campos=(90, 1160, W - 90), stats=(90, 1290, W - 90), stat_h=58, deb=(90, 1560), evid=(560, 1530, W - 90, 1640),
                    pie=(W / 2, H - 110))
    W, H = 1920, 1080
    return dict(W=W, H=H, card=(30, 30, W - 30, H - 30), top=62, titulo=(1450, 150), tsize=92, calav=(1450, 250),
                ventana=(70, 110, 1020, 850), caption=(545, 915), csize=56,
                campos=(1070, 320, W - 80), stats=(1070, 470, W - 80), stat_h=60, deb=(1070, 760), evid=(1460, 730, W - 80, 830),
                pie=(1450, H - 62))


def dibujar_ficha(L, ficha, n, total_fichas, dt, ventana_img, caption_blq, t, ruta_final=None):
    W, H = L["W"], L["H"]
    img = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = L["card"]
    ent = min(1, dt / 0.35)
    off = int((1 - ent) ** 2 * 80)
    d.rectangle([x0, y0 + off, x1, y1 + off], fill=TARJ)
    pulso = 0.75 + 0.25 * math.sin(t * 3)
    neon_rect(img, [x0, y0 + off, x1, y1 + off], MORADO, 4, 12, pulso)
    d = ImageDraw.Draw(img)
    V_ = W < H
    # cabecera
    d.text((x0 + 40, L["top"] + off), f"EXPEDIENTE   #{n:03d}", font=F(ELITE, 34 if V_ else 30), fill=MORADO, anchor="lm")
    d.text((x1 - 40, L["top"] + off), "CASOS QUE NADIE NOTÓ", font=F(ELITE, 30 if V_ else 28), fill=GRIS, anchor="rm")
    especial = ficha in ("comenta", "encuesta", "suscribete")
    if especial:
        data = {"comenta": dict(titulo="CONTINUARÁ...", sello="PARTE 2"),
                "encuesta": dict(titulo="¿QUÉ CASO SIGUE?", sello="TÚ ELIGES"),
                "suscribete": dict(titulo="SUSCRÍBETE", sello="PRÓXIMO CASO")}[ficha]
    else:
        data = FICHAS[ficha]
    # título con efecto máquina de escribir
    tit = data["titulo"]; k = int(len(tit) * min(1, dt / 0.5))
    tx, ty = L["titulo"]
    texto_ajustado(d, (tx, ty + off), tit[:k] + ("_" if k < len(tit) and int(t * 8) % 2 else ""), ANTON, L["tsize"],
                   (x1 - x0) - 80 if V_ else 780, BLANCO, "mm")
    # calaveras
    if not especial:
        cx, cy = L["calav"]
        for i in range(5):
            vis = dt > 0.45 + i * 0.08
            if vis:
                calavera(d, cx - 120 + i * 60, cy + off, 20, i < data["peligro"])
    # ventana con la escena
    vx0, vy0, vx1, vy1 = L["ventana"]
    vw, vh = vx1 - vx0, vy1 - vy0
    if ficha == "encuesta":
        ops = [("1", "EL ROBO DEL LOUVRE"), ("2", "EL CUERPO DE EVITA"), ("3", "DIAMANTES Y UN SÁNDWICH")]
        for i, (num, txt) in enumerate(ops):
            if dt > 0.3 + i * 0.25:
                yy = vy0 + 40 + i * (vh - 80) / 3
                d.rectangle([vx0 + 20, yy, vx1 - 20, yy + (vh - 80) / 3 - 30], fill=MORADO_OSC, outline=MORADO, width=4)
                d.text((vx0 + 70, yy + ((vh - 80) / 3 - 30) / 2), num, font=F(ANTON, 90), fill=BLANCO, anchor="mm")
                texto_ajustado(d, (vx0 + 130, yy + ((vh - 80) / 3 - 30) / 2), txt, ANTON, 60, vw - 180, BLANCO, "lm")
    else:
        img.paste(ventana_img.resize((vw, vh), Image.BILINEAR), (vx0, vy0 + off))
    neon_rect(img, [vx0, vy0 + off, vx1, vy1 + off], MORADO, 3, 8, pulso)
    d = ImageDraw.Draw(img)
    # sello que golpea
    if dt > 0.9:
        u = min(1, (dt - 0.9) / 0.15)
        esc = 2.2 - 1.2 * u
        sello(img, vx1 - (230 if V_ else 260), vy0 + off + 70, data["sello"], 54 if V_ else 50, esc)
        d = ImageDraw.Draw(img)
    # subtítulo karaoke
    if caption_blq is not None:
        pal = [p.upper().strip('"') for p, _, _ in caption_blq["palabras"]]
        act = max([i for i, (_, a, _) in enumerate(caption_blq["palabras"]) if a <= t] or [0])
        f = F(ANTON, L["csize"])
        tot = sum(d.textlength(p + " ", font=f) for p in pal)
        cx, cy = L["caption"]; x = cx - tot / 2
        for i, p in enumerate(pal):
            d.text((x, cy + off), p, font=f, fill=(210, 140, 255) if i == act else BLANCO, anchor="lm",
                   stroke_width=3, stroke_fill=FONDO)
            x += d.textlength(p + " ", font=f)
    if especial:
        msg = {"comenta": 'COMENTA "PARTE 2"', "encuesta": "COMENTA 1, 2 O 3", "suscribete": "SUSCRÍBETE PARA MÁS CASOS"}[ficha]
        px, py = L["pie"]
        texto_ajustado(d, (px, py - (160 if V_ else 60)), msg, ANTON, 90 if V_ else 70, (x1 - x0) - 100, (210, 140, 255), "mm")
        return img
    # campos
    cx0, cy0, cx1 = L["campos"]
    for i, (lab, val) in enumerate(data["campos"]):
        if dt > 0.55 + i * 0.1:
            yy = cy0 + off + i * 52
            d.text((cx0, yy), lab, font=F(ELITE, 32), fill=MORADO, anchor="lm")
            texto_ajustado(d, (cx0 + 250, yy), val, BEBAS, 46, cx1 - cx0 - 250, BLANCO, "lm")
    # barras de estadísticas
    sx0, sy0, sx1 = L["stats"]
    for i, (lab, val) in enumerate(data["stats"]):
        yy = sy0 + off + i * L["stat_h"]
        d.text((sx0, yy), lab, font=F(BEBAS, 44), fill=BLANCO, anchor="lm")
        bx0 = sx0 + 300; seg = (sx1 - bx0) / 5
        llen = max(0, min(5, (dt - 0.6 - i * 0.12) / 0.5 * val))
        for s in range(5):
            box = [bx0 + s * seg + 4, yy - 16, bx0 + (s + 1) * seg - 4, yy + 16]
            if s < llen:
                d.rectangle(box, fill=MORADO)
            else:
                d.rectangle(box, fill=(40, 30, 52))
    # debilidad y evidencia
    dx, dy = L["deb"]
    d.text((dx, dy + off), "DEBILIDAD", font=F(BEBAS, 46), fill=BLANCO, anchor="lm")
    for i in range(3):
        if dt > 1.1 + i * 0.12:
            d.text((dx + 220 + i * 50, dy + off), "?", font=F(ANTON, 54), fill=ROJO, anchor="lm")
    ex0, ey0, ex1, ey1 = L["evid"]
    for xx in range(int(ex0), int(ex1), 18):
        d.line([(xx, ey0 + off), (min(ex1, xx + 9), ey0 + off)], fill=MORADO, width=3)
        d.line([(xx, ey1 + off), (min(ex1, xx + 9), ey1 + off)], fill=MORADO, width=3)
    for yy in range(int(ey0), int(ey1), 18):
        d.line([(ex0, yy + off), (ex0, min(ey1, yy + 9) + off)], fill=MORADO, width=3)
        d.line([(ex1, yy + off), (ex1, min(ey1, yy + 9) + off)], fill=MORADO, width=3)
    d.text(((ex0 + ex1) / 2, ey0 + off + 22), "EVIDENCIA", font=F(ELITE, 26), fill=MORADO, anchor="mm")
    texto_ajustado(d, ((ex0 + ex1) / 2, ey0 + off + 66), data["evidencia"], BEBAS, 44, ex1 - ex0 - 30, BLANCO, "mm")
    # pie
    px, py = L["pie"]
    d.line([(x0 + 40, py - 40 + off), (x1 - 40, py - 40 + off)], fill=MORADO_OSC, width=2)
    d.text((px, py + off), f"PISTA #{n}   ·   CASO SIN RESOLVER", font=F(ELITE, 30), fill=GRIS, anchor="mm")
    return img


def main():
    src, salida, orient, final = sys.argv[1:5]
    data = json.load(open(os.path.join(src, "tiempos.json")))
    frases = data["frases"]; dur = data["duracion"] + 1.5
    L = layout(orient == "vertical")
    W, H = L["W"], L["H"]
    escenas, prev = [], None
    for f in frases:
        e = V.elegir(f["texto"], prev); escenas.append(e); prev = e
    if final == "parte1":
        escenas[-1] = "comenta"
    elif final == "encuesta":
        ini = max(i for i, f in enumerate(frases) if "tú eliges" in f["texto"].lower())
        for i in range(ini, len(frases)):
            escenas[i] = "encuesta"
    elif final == "suscribete":
        for i, f in enumerate(frases):
            if "suscríbete" in f["texto"].lower():
                for j in range(i, len(frases)):
                    escenas[j] = "suscribete"
                break
    fichas = asignar_fichas(frases, escenas)
    # número de expediente por orden de aparición
    nums, orden = {}, []
    for fc in fichas:
        if fc not in nums:
            nums[fc] = len(nums) + 1
    vx0, vy0, vx1, vy1 = L["ventana"]
    vw, vh = vx1 - vx0, vy1 - vy0
    cache = {}
    def ventana(e):
        if e not in cache:
            V.LABEL_Y = 0.10
            cache[e] = V.escena(e if e not in ("comenta", "encuesta", "suscribete") else "peron", int(vw * 1.1), int(vh * 1.1))
        return cache[e]
    blq = V.bloques(frases)
    ini_ficha, ini_escena = [], []
    for i in range(len(frases)):
        if i == 0 or fichas[i] != fichas[i - 1]:
            ini_ficha.append(frases[i]["ini"])
        if i == 0 or escenas[i] != escenas[i - 1]:
            ini_escena.append(frases[i]["ini"])
    sellos = [t + 0.9 for t in ini_ficha]
    ruta_sfx = os.path.join(src, "sfx_ficha.wav")
    V.sfx(ini_ficha + ini_escena, sellos, dur, ruta_sfx)
    rng = np.random.default_rng(5)
    granos = [rng.normal(0, 9, (H // 2, W // 2)).astype(np.int16).repeat(2, 0).repeat(2, 1)[:H, :W, None] for _ in range(4)]
    scan = np.ones((H, W, 1), np.float32); scan[::4] = 0.88
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", os.path.join(src, "voz.wav"), "-i", ruta_sfx,
           "-filter_complex", f"anoisesrc=c=brown:a=0.02:d={dur},lowpass=f=180,volume=0.5[n];"
                              f"sine=f=55:d={dur},volume=0.025[s1];[n][s1]amix=2:normalize=0,afade=t=in:d=2[bg];"
                              "[1:a]apad[v];[2:a]volume=0.9[fx];[v][bg][fx]amix=3:normalize=0:duration=shortest[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-b:v", "8M" if W < H else "6M",
           "-maxrate", "9M", "-bufsize", "4M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.2f}", "-movflags", "+faststart", salida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fi = bi = 0; t_ficha = 0.0; t_esc = 0.0
    shake = random.Random(3)
    for k in range(int(dur * FPS)):
        t = k / FPS
        while fi + 1 < len(frases) and t >= frases[fi + 1]["ini"]:
            fi += 1
            if fichas[fi] != fichas[fi - 1]:
                t_ficha = frases[fi]["ini"]
            if escenas[fi] != escenas[fi - 1]:
                t_esc = frases[fi]["ini"]
        dt = t - t_ficha
        src_img = ventana(escenas[fi])
        z = 1.0 + 0.06 * min(1, (t - t_esc) / 6)
        sw, sh = src_img.size; cw, ch = sw / (1.1 * z), sh / (1.1 * z)
        ox = (sw - cw) / 2 + math.sin(t * 0.4) * 8; oy = (sh - ch) / 2
        win = src_img.crop((int(ox), int(oy), int(ox + cw), int(oy + ch)))
        if t - t_esc < 0.12 and fi > 0:
            win = Image.blend(win, Image.new("RGB", win.size, (230, 200, 255)), 0.5 * (1 - (t - t_esc) / 0.12))
        while bi + 1 < len(blq) and t >= blq[bi + 1]["ini"]:
            bi += 1
        cap = blq[bi] if blq[bi]["ini"] - 0.05 <= t <= blq[bi]["fin"] + 0.35 else None
        img = dibujar_ficha(L, fichas[fi], nums[fichas[fi]], len(nums), dt, win, cap, t)
        arr = np.asarray(img).astype(np.int16)
        # glitch RGB al entrar una ficha
        if dt < 0.2:
            s = int((0.2 - dt) * 60)
            arr[..., 0] = np.roll(arr[..., 0], s, axis=1); arr[..., 2] = np.roll(arr[..., 2], -s, axis=1)
        # temblor cuando golpea el sello
        if 0.9 < dt < 1.15:
            a = int((1.15 - dt) * 50)
            arr = np.roll(arr, (shake.randint(-a, a), shake.randint(-a, a)), axis=(0, 1))
        arr = (arr + granos[(k // 2) % 4]) * scan
        p.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
        if k % (FPS * 60) == 0:
            print(f"{t:6.0f}s / {dur:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("listo", salida)


if __name__ == "__main__":
    main()
