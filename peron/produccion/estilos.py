"""Genera 10 muestras de estilos de personajes (Perón, Evita y el ladrón en el cementerio).

Uso: FONTS_DIR=... python3 estilos.py <carpeta_salida>
"""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

os.environ.pop("PERSONAJES", None)
import video as V
import personajes as P

W, H = 1280, 720
ELENCO = [("peron", "feliz", "uno", 1), ("evita", "feliz", "abajo", 1), ("ladron", "enojo", "frente", -1)]
XS = [0.27, 0.5, 0.75]


def fondo():
    img = Image.new("RGB", (W, H))
    piso = V.fondo(img, "noche")
    d = ImageDraw.Draw(img)
    for x in (0.08, 0.38, 0.62, 0.93):
        cx = W * x
        d.rectangle([cx - 14, piso - 120, cx + 14, piso], fill=(95, 95, 105), outline=(20, 20, 24), width=3)
        d.rectangle([cx - 45, piso - 100, cx + 45, piso - 76], fill=(95, 95, 105), outline=(20, 20, 24), width=3)
    return V.post(img), piso


def rotulo(img, n, nombre):
    d = ImageDraw.Draw(img)
    f = V.F(V.ANTON, 64)
    txt = f"{n}"
    d.rounded_rectangle([24, 22, 124, 112], 16, fill=V.ROJO, outline=(10, 10, 10), width=4)
    d.text((74, 66), txt, font=f, fill="white", anchor="mm")
    f2 = V.F(V.ELITE, 40)
    tw = d.textlength(nombre, font=f2)
    d.rectangle([140, 40, 140 + tw + 30, 96], fill=(10, 10, 12), outline=V.ROJO, width=3)
    d.text((155, 68), nombre, font=f2, fill=(240, 70, 70), anchor="lm")
    return img


def pegar(img, sp, x, pie_y, alto):
    f = alto / 760
    sp = sp.resize((int(sp.size[0] * f), int(sp.size[1] * f)), Image.LANCZOS)
    img.paste(sp, (int(x - P.PIES[0] * f), int(pie_y - P.PIES[1] * f)), sp)


def sprites(transform=None, luz=(255, 200, 140)):
    out = []
    for t, h, b, m in ELENCO:
        sp = P.sprite(t, h, False, b, m, luz).copy()
        out.append(transform(sp) if transform else sp)
    return out


def escena_con(sps, alto=430, bg=None):
    img, piso = bg if bg else fondo()
    img = img.copy()
    for sp, x in zip(sps, XS):
        pegar(img, sp, W * x, piso + 8, alto)
    return img


# ---------------------------------------------------------------- estilos
def e1():
    return escena_con(sprites())


def e2():
    img, piso = fondo()
    d = ImageDraw.Draw(img)
    for (t, h, b, m), x in zip(ELENCO, XS):
        V.monigote(d, W * x, piso + 8, 0.75, t, b, mira=m)
    return img


def e3():  # papel recortado
    def papel(sp):
        a = sp.getchannel("A").point(lambda v: 255 if v > 90 else 0)
        borde = a.filter(ImageFilter.MaxFilter(17))
        base = Image.new("RGBA", sp.size, (0, 0, 0, 0))
        sombra = borde.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.6))
        base.paste(Image.new("RGBA", sp.size, (0, 0, 0, 255)), (14, 18), sombra)
        base.paste(Image.new("RGBA", sp.size, (250, 246, 236, 255)), (0, 0), borde)
        cuerpo = Image.new("RGBA", sp.size, (0, 0, 0, 0))
        cuerpo.paste(sp, (0, 0), a)
        tex = Image.effect_noise(sp.size, 30).convert("RGB")
        rgb = ImageChops.multiply(cuerpo.convert("RGB"), ImageOps.autocontrast(tex, cutoff=40).point(lambda v: 200 + v // 5))
        base.paste(rgb, (0, 0), a)
        return base.rotate(random.uniform(-6, 6), resample=Image.BICUBIC)
    random.seed(2)
    img, piso = fondo()
    tex = Image.effect_noise((W, H), 25).convert("RGB")
    img = ImageChops.multiply(img, tex.point(lambda v: 205 + v // 5))
    return escena_con(sprites(papel), bg=(img, piso))


def e4():  # cómic noir con tramado
    def comic(sp):
        a = sp.getchannel("A")
        rgb = np.asarray(sp.convert("RGB")).astype(np.float32)
        g = rgb.mean(axis=2)
        roj = (rgb[..., 0] > rgb[..., 1] * 1.5) & (rgb[..., 0] > 120)
        out = np.where(g > 170, 245, np.where(g > 90, 150, 15)).astype(np.float32)
        yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
        puntos = ((xx % 10 - 5) ** 2 + (yy % 10 - 5) ** 2) < 10
        out = np.where((out == 150) & puntos, 15, np.where(out == 150, 245, out))
        res = np.stack([out] * 3, axis=2)
        res[roj] = [215, 25, 35]
        im = Image.fromarray(res.astype(np.uint8)).convert("RGBA")
        im.putalpha(a)
        return im
    img, piso = fondo()
    img = ImageOps.grayscale(img).convert("RGB")
    img = Image.blend(img, Image.new("RGB", (W, H), (120, 10, 20)), 0.35)
    return escena_con(sprites(comic, luz=(255, 255, 255)), bg=(img, piso))


def e5():  # pixel art
    img = escena_con(sprites())
    p = img.resize((W // 8, H // 8), Image.NEAREST).quantize(32).convert("RGB")
    return p.resize((W, H), Image.NEAREST)


def e6():  # neón
    def neon(sp, col):
        a = sp.getchannel("A")
        lum = ImageOps.grayscale(sp.convert("RGB"))
        bordes = ImageChops.lighter(lum.filter(ImageFilter.FIND_EDGES), a.filter(ImageFilter.FIND_EDGES))
        bordes = bordes.point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(3))
        out = Image.new("RGBA", sp.size, (0, 0, 0, 0))
        glow = bordes.filter(ImageFilter.GaussianBlur(9))
        out.paste(Image.new("RGBA", sp.size, col + (255,)), (0, 0), glow)
        out.paste(Image.new("RGBA", sp.size, col + (255,)), (0, 0), glow)
        out.paste(Image.new("RGBA", sp.size, (255, 255, 255, 255)), (0, 0), bordes)
        return out
    cols = [(60, 220, 255), (255, 70, 200), (255, 60, 60)]
    sps = [neon(P.sprite(t, h, False, b, m).copy(), c) for (t, h, b, m), c in zip(ELENCO, cols)]
    img = Image.new("RGB", (W, H), (6, 4, 14))
    d = ImageDraw.Draw(img)
    for k in range(0, W, 80):
        d.line([(k, H * 0.86), (W / 2 + (k - W / 2) * 3, H)], fill=(80, 20, 120), width=2)
    for k in range(6):
        y = H * 0.86 + k * k * 4
        d.line([(0, y), (W, y)], fill=(80, 20, 120), width=2)
    return escena_con(sps, bg=(img, int(H * 0.86)))


def e7():  # boceto a lápiz
    def lapiz(sp):
        a = sp.getchannel("A")
        g = ImageOps.grayscale(sp.convert("RGB"))
        linea = ImageOps.invert(g.filter(ImageFilter.FIND_EDGES)).point(lambda v: 40 if v < 200 else 255)
        sombra = g.point(lambda v: 200 if v < 110 else 255)
        rnd = np.random.default_rng(1)
        rayado = np.ones(g.size[::-1]) * 255
        yy, xx = np.mgrid[0:g.size[1], 0:g.size[0]]
        rayado[(xx + yy) % 9 == 0] = 140
        oscuro = np.asarray(g) < 70
        som = np.minimum(np.asarray(sombra), np.where(np.asarray(sombra) < 255, rayado, 255))
        cruz = np.where(((xx - yy) % 6 == 0) | ((xx + yy) % 6 == 0), 70, 235)
        som = np.where(oscuro, cruz, som)
        res = np.minimum(np.asarray(linea), som).astype(np.uint8)
        im = Image.fromarray(res).convert("RGB")
        im = Image.blend(im, Image.new("RGB", im.size, (60, 50, 40)), 0.08).convert("RGBA")
        im.putalpha(a.point(lambda v: 255 if v > 100 else 0))
        return im
    papel = Image.new("RGB", (W, H), (236, 226, 204))
    papel = ImageChops.multiply(papel, Image.effect_noise((W, H), 20).convert("RGB").point(lambda v: 215 + v // 6))
    d = ImageDraw.Draw(papel)
    piso = int(H * 0.84)
    d.line([(0, piso), (W, piso)], fill=(70, 60, 50), width=3)
    for x in (0.08, 0.93):
        d.line([(W * x, piso), (W * x, piso - 120)], fill=(70, 60, 50), width=5)
        d.line([(W * x - 40, piso - 95), (W * x + 40, piso - 95)], fill=(70, 60, 50), width=5)
    return escena_con(sprites(lapiz, luz=(236, 226, 204)), bg=(papel, piso))


def e8():  # chibi: cabeza enorme, cuerpo mini
    def chibi(sp):
        w, h = sp.size
        corte = 440
        cab = sp.crop((0, 0, w, corte)).resize((int(w * 1.3), int(corte * 1.3)), Image.LANCZOS)
        cue = sp.crop((0, corte, w, h)).resize((int(w * 0.7), int((h - corte) * 0.55)), Image.LANCZOS)
        out = Image.new("RGBA", (int(w * 1.3), h), (0, 0, 0, 0))
        oy = h - cue.size[1]
        out.alpha_composite(cue, ((out.size[0] - cue.size[0]) // 2, oy))
        out.alpha_composite(cab, (0, oy - cab.size[1] + 40))
        # brillos extra en los ojos
        return out
    return escena_con(sprites(chibi), alto=400)


def e9():  # frijolitos
    img, piso = fondo()
    img = img.copy()
    d = ImageDraw.Draw(img)
    datos = [((115, 128, 70), "militar", (24, 22, 28)), ((245, 240, 232), "mono", (250, 205, 70)), ((30, 30, 36), "mascara", (30, 30, 36))]
    for (col, acc, pelo), x in zip(datos, XS):
        cx = W * x; base = piso + 6; bw, bh = 120, 260
        d.ellipse([cx - bw - 6, base - 18, cx + bw + 6, base + 18], fill=(8, 8, 10))
        d.rounded_rectangle([cx - bw, base - bh * 1.45, cx + bw, base], radius=bw, fill=col, outline=(20, 16, 20), width=7)
        d.rounded_rectangle([cx + bw * 0.35, base - bh * 1.4, cx + bw - 8, base - 10], radius=bw, fill=tuple(int(v * 0.82) for v in col))
        fy = base - bh * 1.05
        if acc == "mascara":
            d.rounded_rectangle([cx - 85, fy - 40, cx + 85, fy + 30], 30, fill=(244, 196, 150), outline=(20, 16, 20), width=5)
        for ex in (cx - 40, cx + 40):
            d.ellipse([ex - 26, fy - 30, ex + 26, fy + 26], fill="white", outline=(20, 16, 20), width=5)
            d.ellipse([ex - 10, fy - 10, ex + 14, fy + 16], fill=(15, 10, 10))
            d.ellipse([ex - 6, fy - 8, ex + 2, fy], fill="white")
        if acc == "militar":
            top = base - bh * 1.45
            d.polygon([(cx - 120, top + 60), (cx - 135, top - 30), (cx + 140, top - 40), (cx + 125, top + 60)], fill=(110, 120, 66), outline=(20, 16, 20))
            d.rectangle([cx - 125, top + 40, cx + 128, top + 62], fill=(250, 205, 60), outline=(20, 16, 20), width=3)
            d.polygon([(cx - 20, top + 62), (cx + 160, top + 72), (cx + 140, top + 92), (cx - 10, top + 80)], fill=(18, 18, 22))
            d.arc([cx - 45, fy + 30, cx + 45, fy + 80], 10, 170, fill=(20, 16, 20), width=7)
            d.line([(cx - 110, base - bh * 1.1), (cx + 110, base - 60)], fill=(108, 172, 228), width=22)
            d.line([(cx - 110, base - bh * 1.1), (cx + 110, base - 60)], fill="white", width=6)
        elif acc == "mono":
            top = base - bh * 1.45
            d.ellipse([cx - 60, top - 80, cx + 60, top + 30], fill=pelo, outline=(20, 16, 20), width=6)
            d.chord([cx - bw, top, cx + bw, top + 150], 180, 360, fill=pelo, outline=(20, 16, 20), width=6)
            d.chord([cx - 40, fy + 30, cx + 40, fy + 80], 0, 180, fill=(215, 30, 50), outline=(20, 16, 20), width=5)
        else:
            d.line([(cx - 60, fy - 52), (cx - 15, fy - 38)], fill=(20, 16, 20), width=9)
            d.line([(cx + 60, fy - 52), (cx + 15, fy - 38)], fill=(20, 16, 20), width=9)
    return img


def e10():  # plastilina / 3D suave
    def clay(sp):
        a = np.asarray(sp.getchannel("A")).astype(np.float32) / 255
        h = np.asarray(sp.getchannel("A").filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
        lum = np.asarray(ImageOps.grayscale(sp.convert("RGB")).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
        h = h * 0.7 + lum * 0.3
        gy, gx = np.gradient(h)
        shade = np.clip(1 + (gx * 0.7 + gy * 0.7) * 22, 0.45, 1.6)
        spec = np.clip((-gx * 0.7 - gy * 0.7) * 60 - 0.4, 0, 1) * 140
        rgb = np.asarray(sp.convert("RGB").filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
        rgb = rgb * shade[..., None] + spec[..., None]
        rgb += np.random.default_rng(3).normal(0, 5, rgb.shape)
        im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
        im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        return im
    return escena_con(sprites(clay))


ESTILOS = [(e1, "CARICATURA CABEZONA"), (e2, "SILUETAS NOIR"), (e3, "PAPEL RECORTADO"), (e4, "CÓMIC NOIR"),
           (e5, "PIXEL ART"), (e6, "NEÓN"), (e7, "BOCETO A LÁPIZ"), (e8, "CHIBI"), (e9, "FRIJOLITOS"),
           (e10, "PLASTILINA 3D")]


def _filtro_pintura(sp, tam=7, sat=1.0, textura=40):
    from PIL import ImageEnhance
    a = sp.getchannel("A")
    rgb = sp.convert("RGB").filter(ImageFilter.ModeFilter(tam)).filter(ImageFilter.SMOOTH_MORE)
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    tex = Image.effect_noise(sp.size, textura).convert("RGB").filter(ImageFilter.EMBOSS)
    rgb = Image.blend(rgb, ImageChops.overlay(rgb, tex), 0.35)
    im = rgb.convert("RGBA"); im.putalpha(a)
    return im


def e11():  # monigote de palitos
    img, piso = fondo(); img = img.copy(); d = ImageDraw.Draw(img)
    for (t, _, b, m), x in zip(ELENCO, XS):
        cx = W * x; base = piso + 6; ink = (245, 245, 245) if t != "ladron" else (240, 70, 70)
        hy = base - 330
        d.line([(cx, hy + 70), (cx, base - 140)], fill=ink, width=9)
        d.line([(cx, base - 140), (cx - 45, base)], fill=ink, width=9); d.line([(cx, base - 140), (cx + 45, base)], fill=ink, width=9)
        brazo = {"uno": (cx + 80, hy - 20), "frente": (cx - 110 if m < 0 else cx + 110, hy + 120)}.get(b, (cx + 70, hy + 190))
        d.line([(cx, hy + 120), (cx - 70, hy + 190)], fill=ink, width=9); d.line([(cx, hy + 120), brazo], fill=ink, width=9)
        d.ellipse([cx - 70, hy - 70, cx + 70, hy + 70], fill=(250, 250, 250), outline=(20, 20, 20), width=8)
        for ex in (cx - 24, cx + 24):
            d.ellipse([ex - 9, hy - 14, ex + 9, hy + 6], fill=(20, 20, 20))
        if t == "peron":
            d.polygon([(cx - 75, hy - 40), (cx - 85, hy - 105), (cx + 85, hy - 112), (cx + 75, hy - 40)], fill=(110, 120, 66), outline=(20, 20, 20))
            d.polygon([(cx - 10, hy - 40), (cx + 110, hy - 34), (cx + 95, hy - 20), (cx - 5, hy - 26)], fill=(20, 20, 20))
            d.arc([cx - 35, hy + 5, cx + 35, hy + 45], 10, 170, fill=(20, 20, 20), width=6)
            d.line([(cx - 25, hy + 100), (cx + 25, hy + 180)], fill=(108, 172, 228), width=14)
        elif t == "evita":
            d.ellipse([cx - 45, hy - 125, cx + 45, hy - 45], fill=(250, 205, 70), outline=(20, 20, 20), width=6)
            d.polygon([(cx - 40, hy + 160), (cx + 40, hy + 160), (cx + 70, base - 90), (cx - 70, base - 90)], fill=(245, 245, 245), outline=(20, 20, 20))
            d.arc([cx - 30, hy + 10, cx + 30, hy + 40], 10, 170, fill=(215, 30, 50), width=6)
        else:
            d.chord([cx - 70, hy - 10, cx + 70, hy + 70], 0, 180, fill=(20, 20, 24))
            d.line([(cx - 40, hy - 34), (cx - 10, hy - 22)], fill=(20, 20, 20), width=7); d.line([(cx + 40, hy - 34), (cx + 10, hy - 22)], fill=(20, 20, 20), width=7)
    return img


def e12():  # óleo
    img, piso = fondo()
    img = escena_con(sprites(lambda sp: _filtro_pintura(sp, 9, 0.85, 50)), bg=(img, piso))
    return Image.blend(img.filter(ImageFilter.ModeFilter(5)), Image.new("RGB", img.size, (60, 40, 20)), 0.12)


def e13():  # acuarela
    def acua(sp):
        a = sp.getchannel("A")
        rgb = sp.convert("RGB").filter(ImageFilter.GaussianBlur(3))
        rgb = Image.blend(rgb, Image.new("RGB", sp.size, (255, 255, 255)), 0.25)
        bordes = ImageOps.invert(ImageOps.grayscale(sp.convert("RGB")).filter(ImageFilter.FIND_EDGES)).point(lambda v: 255 if v > 200 else 120)
        rgb = ImageChops.multiply(rgb, Image.merge("RGB", (bordes,) * 3))
        im = rgb.convert("RGBA"); im.putalpha(a.filter(ImageFilter.GaussianBlur(2)))
        return im
    papel = Image.new("RGB", (W, H), (240, 232, 215))
    capa = Image.new("RGB", (W, H), (240, 232, 215)); d = ImageDraw.Draw(capa)
    d.ellipse([W * 0.7, -100, W * 1.1, H * 0.5], fill=(170, 180, 215)); d.rectangle([0, H * 0.84, W, H], fill=(150, 140, 125))
    papel = Image.blend(papel, capa.filter(ImageFilter.GaussianBlur(40)), 0.8)
    papel = ImageChops.multiply(papel, Image.effect_noise((W, H), 30).convert("RGB").point(lambda v: 215 + v // 6))
    return escena_con(sprites(acua, luz=(240, 232, 215)), bg=(papel, int(H * 0.84)))


def e14():  # anime suave pastel
    def anime(sp):
        from PIL import ImageEnhance
        a = sp.getchannel("A")
        rgb = ImageEnhance.Brightness(sp.convert("RGB")).enhance(1.12)
        rgb = Image.blend(rgb, Image.new("RGB", sp.size, (255, 220, 235)), 0.18)
        im = rgb.convert("RGBA"); im.putalpha(a)
        return im
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(60 + 140 * t), int(40 + 60 * t), int(120 + 60 * t)))
    rnd = random.Random(4)
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.7)); r = rnd.choice((2, 3, 5))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 250))
    d.rectangle([0, H * 0.84, W, H], fill=(70, 50, 90))
    return escena_con(sprites(anime, luz=(255, 190, 230)), bg=(img, int(H * 0.84)))


def e15():  # 3D tipo película animada (sombreado esférico fuerte)
    def tres_d(sp):
        a = np.asarray(sp.getchannel("A")).astype(np.float32) / 255
        rgb = np.asarray(sp.convert("RGB")).astype(np.float32)
        h = np.asarray(sp.getchannel("A").filter(ImageFilter.GaussianBlur(28))).astype(np.float32) / 255
        gy, gx = np.gradient(h)
        luz = np.clip(0.75 + (gx * 0.6 + gy * 0.8) * -35 + h * 0.35, 0.35, 1.45)
        spec = np.clip((-gx * 0.6 - gy * 0.8) * 90 - 0.6, 0, 1) * 120
        rgb = rgb * luz[..., None] + spec[..., None]
        im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).filter(ImageFilter.SMOOTH).convert("RGBA")
        im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        return im
    return escena_con(sprites(tres_d))


def e16():  # cómic oscuro con sombras duras
    def duro(sp):
        a = sp.getchannel("A")
        rgb = sp.convert("RGB").quantize(8).convert("RGB")
        w, h = sp.size
        m = Image.new("L", sp.size, 0); ImageDraw.Draw(m).polygon([(w * 0.55, 0), (w, 0), (w, h), (w * 0.62, h)], fill=150)
        rgb.paste((10, 10, 14), (0, 0), ImageChops.multiply(m, a))
        bordes = ImageOps.grayscale(sp.convert("RGB")).filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 30 else 0).filter(ImageFilter.MaxFilter(3))
        rgb.paste((0, 0, 0), (0, 0), bordes)
        im = rgb.convert("RGBA"); im.putalpha(a)
        return im
    img, piso = fondo()
    img = Image.blend(img, Image.new("RGB", (W, H), (90, 0, 10)), 0.3)
    return escena_con(sprites(duro, luz=(255, 60, 60)), bg=(img, piso))


def e17():  # póster de propaganda años 40
    def poster(sp):
        a = sp.getchannel("A")
        g = ImageOps.grayscale(sp.convert("RGB"))
        pal = [(30, 25, 25), (180, 35, 35), (235, 220, 190)]
        arr = np.asarray(g)
        out = np.zeros(arr.shape + (3,), np.uint8)
        out[arr < 70] = pal[0]; out[(arr >= 70) & (arr < 160)] = pal[1]; out[arr >= 160] = pal[2]
        im = Image.fromarray(out).convert("RGBA"); im.putalpha(a)
        return im
    img = Image.new("RGB", (W, H), (235, 220, 190)); d = ImageDraw.Draw(img)
    for k in range(0, 360, 12):
        import math
        d.polygon([(W / 2, H * 0.55), (W / 2 + math.cos(math.radians(k)) * 1500, H * 0.55 + math.sin(math.radians(k)) * 1500),
                   (W / 2 + math.cos(math.radians(k + 6)) * 1500, H * 0.55 + math.sin(math.radians(k + 6)) * 1500)], fill=(215, 190, 150))
    d.rectangle([0, H * 0.84, W, H], fill=(30, 25, 25))
    return escena_con(sprites(poster, luz=(235, 220, 190)), bg=(img, int(H * 0.84)))


def e18():  # grabado / linóleo
    def grabado(sp):
        a = sp.getchannel("A")
        g = np.asarray(ImageOps.grayscale(sp.convert("RGB"))).astype(np.int16)
        yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
        lineas = (np.sin(yy * 0.9 + np.sin(xx * 0.05) * 3) + 1) * 127
        tinta = g < lineas * 0.8
        out = np.where(tinta, 25, 238).astype(np.uint8)
        im = Image.fromarray(out).convert("RGB")
        im = ImageChops.multiply(im, Image.new("RGB", im.size, (245, 235, 215))).convert("RGBA"); im.putalpha(a)
        return im
    img = Image.new("RGB", (W, H), (240, 230, 210)); d = ImageDraw.Draw(img)
    for y in range(0, H, 7):
        d.line([(0, y), (W, y)], fill=(215, 205, 185), width=2)
    d.rectangle([0, H * 0.84, W, H], fill=(25, 25, 25))
    return escena_con(sprites(grabado, luz=(240, 230, 210)), bg=(img, int(H * 0.84)))


def e19():  # tiza en pizarra
    def tiza(sp):
        a = sp.getchannel("A")
        g = ImageOps.grayscale(sp.convert("RGB"))
        b = ImageChops.lighter(g.filter(ImageFilter.FIND_EDGES), a.filter(ImageFilter.FIND_EDGES)).point(lambda v: 255 if v > 35 else 0)
        b = b.filter(ImageFilter.MaxFilter(3))
        ruido = Image.effect_noise(sp.size, 120).point(lambda v: 255 if v > 110 else 60)
        b = ImageChops.multiply(b, ruido)
        relleno = ImageChops.multiply(a.point(lambda v: 40 if v > 128 else 0), ruido)
        col = Image.new("RGBA", sp.size, (0, 0, 0, 0))
        col.paste(Image.new("RGBA", sp.size, (250, 250, 240, 255)), (0, 0), ImageChops.lighter(b, relleno))
        return col
    img = Image.new("RGB", (W, H), (32, 58, 46))
    img = ImageChops.add(img, Image.effect_noise((W, H), 18).convert("RGB").point(lambda v: v // 10))
    d = ImageDraw.Draw(img); d.line([(0, H * 0.84), (W, H * 0.84)], fill=(220, 220, 210), width=4)
    d.rectangle([0, 0, W, 16], fill=(110, 75, 40)); d.rectangle([0, H - 16, W, H], fill=(110, 75, 40))
    return escena_con(sprites(tiza, luz=(32, 58, 46)), bg=(img, int(H * 0.84)))


def e20():  # caricatura editorial pintada (cabezona + pintura)
    return escena_con(sprites(lambda sp: _filtro_pintura(sp, 5, 1.15, 30)), alto=450)


ESTILOS += [(e11, "MONIGOTE DE PALITOS"), (e12, "ÓLEO"), (e13, "ACUARELA"), (e14, "ANIME PASTEL"),
            (e15, "3D TIPO PELÍCULA"), (e16, "CÓMIC OSCURO"), (e17, "PÓSTER AÑOS 40"), (e18, "GRABADO"),
            (e19, "TIZA EN PIZARRA"), (e20, "CARICATURA PINTADA")]

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for i, (fn, nombre) in enumerate(ESTILOS, 1):
        img = rotulo(fn(), i, nombre)
        img.save(os.path.join(out, f"estilo-{i:02d}.png"))
        print(i, nombre)
