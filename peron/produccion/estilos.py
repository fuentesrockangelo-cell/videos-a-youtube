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
        som = np.minimum(np.asarray(sombra), np.where(np.asarray(sombra) < 255, rayado, 255))
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
        shade = np.clip(1 + (-gx * -0.7 + -gy * -0.7) * 9, 0.55, 1.5)
        spec = np.clip((-gx * 0.7 - gy * 0.7) * 30 - 0.5, 0, 1) * 90
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

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for i, (fn, nombre) in enumerate(ESTILOS, 1):
        img = rotulo(fn(), i, nombre)
        img.save(os.path.join(out, f"estilo-{i:02d}.png"))
        print(i, nombre)
