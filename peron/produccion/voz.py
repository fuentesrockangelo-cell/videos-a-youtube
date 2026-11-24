"""Genera la voz en off de un guion y los tiempos de cada frase.

Uso: python3 voz.py guion.txt salida_dir
Produce salida_dir/voz.wav y salida_dir/tiempos.json
"""
import json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("PIPER_MODEL")  # ruta al .onnx (es_MX-ald-medium)
SR = 22050
PAUSA_FRASE = 0.32
PAUSA_PARRAFO = 0.55
EQ_RASPUTIN = "100:5|125:4|160:5|200:5|250:6|315:2|500:-1|630:-2|1600:2|2000:7|2500:3|4000:7|5000:5|10000:-3"
FX_LOCUTOR = ("highpass=f=75,firequalizer=gain_entry='" +
              ";".join(f"entry({b},{g})" for b, g in (x.split(":") for x in EQ_RASPUTIN.split("|"))) + "',"
              "deesser=i=0.4,acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=3,"
              "aecho=0.8:0.35:22:0.05,alimiter=limit=0.9,loudnorm=I=-14:TP=-1.2:LRA=9")
FX = ("highpass=f=70,equalizer=f=180:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1.5:g=2,"
      "acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
      "aecho=0.8:0.4:28:0.07,loudnorm=I=-16:TP=-1.5")


def frases(texto):
    out = []
    for p in [p.strip() for p in texto.split("\n\n") if p.strip()]:
        partes = re.findall(r'[^.?!…]+(?:\.\.\.|[.?!…])*"?', p.replace("\n", " "))
        partes = [s.strip() for s in partes if s.strip()]
        # une trozos muy cortos ("Tres veces.") con el anterior solo si son de 1 palabra
        for i, s in enumerate(partes):
            out.append({"texto": s, "fin_parrafo": i == len(partes) - 1})
    return out


KOKORO = os.environ.get("KOKORO_DIR")  # carpeta kokoro-multi-lang-v1_0 (voz natural, recomendada)
KOKORO_VOZ = int(os.environ.get("KOKORO_VOZ", "29"))  # 29 = em_alex (hombre, español)


def sintetizador():
    global SR
    if KOKORO:
        import sherpa_onnx
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=f"{KOKORO}/model.onnx", voices=f"{KOKORO}/voices.bin", tokens=f"{KOKORO}/tokens.txt",
                data_dir=f"{KOKORO}/espeak-ng-data", lang="es"), num_threads=8))
        tts = sherpa_onnx.OfflineTts(cfg)
        SR = tts.sample_rate
        def say(texto):
            emo = emocion(texto)
            a = np.asarray(tts.generate(texto, sid=KOKORO_VOZ, speed=emo["vel"]).samples, dtype=np.float32)
            return a * 10 ** (emo["db"] / 20)
        return say
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(MODEL)
    cfg = SynthesisConfig(length_scale=1.1, noise_scale=0.85, noise_w_scale=1.0)
    return lambda texto: np.concatenate([c.audio_float_array for c in voice.synthesize(texto, syn_config=cfg)])


SUSPENSO = ("nadie", "nunca", "muerto", "muere", "asesinado", "oscura", "misterio", "noche", "manos", "tumba", "ataúd")


def emocion(texto):
    """Ritmo y volumen de locutor según lo que dice la frase."""
    t = texto.lower(); n = len(t.split())
    if t.endswith("..."):
        return dict(vel=0.84, db=-2.0)          # suspenso: lento y más bajo
    if t.endswith("?"):
        return dict(vel=0.88, db=0.0)           # pregunta al espectador
    if n <= 5:
        return dict(vel=0.92, db=+2.0)          # golpe corto: con fuerza
    if any(w in t for w in SUSPENSO):
        return dict(vel=0.86, db=-1.0)          # tensión
    return dict(vel=0.93, db=0.0)               # narración


def pausa_tras(f):
    t = f["texto"]
    if f["fin_parrafo"]:
        return 0.7
    if t.endswith("..."):
        return 0.6
    if t.endswith("?"):
        return 0.45
    return PAUSA_FRASE


def main():
    guion, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    say = sintetizador()
    lista = frases(open(guion, encoding="utf-8").read())
    audio, t = [], 0.0
    for f in lista:
        a = say(f["texto"].replace('"', ""))
        # recorta silencios del motor al inicio y al final
        nz = np.where(np.abs(a) > 0.01)[0]
        if len(nz):
            a = a[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.08 * SR)]
        f["ini"] = t
        t += len(a) / SR
        f["fin"] = t
        audio.append(a)
        pausa = pausa_tras(f)
        audio.append(np.zeros(int(pausa * SR), dtype=np.float32))
        t += pausa
    a = np.concatenate(audio)
    a = (a / max(1e-6, np.abs(a).max()) * 0.9 * 32767).astype(np.int16)
    raw = os.path.join(outdir, "voz_cruda.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())
    expr = os.path.join(outdir, "voz_expr.wav")
    if KOKORO:
        expr = raw  # la voz ya es natural: no se fuerza la entonación
    else:
        subprocess.run([sys.executable, os.path.join(HERE, "expresion.py"), raw, expr, "132", "1.9"], check=True)
    fx = FX_LOCUTOR if os.environ.get("VOZ_ESTILO") == "locutor" else FX
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", expr, "-af", fx, "-ar", "44100",
                    os.path.join(outdir, "voz.wav")], check=True)
    json.dump({"frases": lista, "duracion": t}, open(os.path.join(outdir, "tiempos.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(lista)} frases, {t/60:.2f} min")


if __name__ == "__main__":
    main()
