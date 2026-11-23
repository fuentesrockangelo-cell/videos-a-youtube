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
FX = ("highpass=f=70,equalizer=f=180:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1.5:g=2,"
      "acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
      "aecho=0.8:0.5:35:0.12,loudnorm=I=-16:TP=-1.5")


def frases(texto):
    out = []
    for p in [p.strip() for p in texto.split("\n\n") if p.strip()]:
        partes = re.findall(r'[^.?!…]+(?:\.\.\.|[.?!…])*"?', p.replace("\n", " "))
        partes = [s.strip() for s in partes if s.strip()]
        # une trozos muy cortos ("Tres veces.") con el anterior solo si son de 1 palabra
        for i, s in enumerate(partes):
            out.append({"texto": s, "fin_parrafo": i == len(partes) - 1})
    return out


def main():
    from piper import PiperVoice, SynthesisConfig
    guion, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    voice = PiperVoice.load(MODEL)
    cfg = SynthesisConfig(length_scale=1.1, noise_scale=0.85, noise_w_scale=1.0)
    lista = frases(open(guion, encoding="utf-8").read())
    audio, t = [], 0.0
    for f in lista:
        chunks = list(voice.synthesize(f["texto"], syn_config=cfg))
        a = np.concatenate([c.audio_float_array for c in chunks])
        f["ini"] = t
        t += len(a) / SR
        f["fin"] = t
        audio.append(a)
        pausa = PAUSA_PARRAFO if f["fin_parrafo"] else PAUSA_FRASE
        audio.append(np.zeros(int(pausa * SR), dtype=np.float32))
        t += pausa
    a = np.concatenate(audio)
    a = (a / max(1e-6, np.abs(a).max()) * 0.9 * 32767).astype(np.int16)
    raw = os.path.join(outdir, "voz_cruda.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())
    expr = os.path.join(outdir, "voz_expr.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "expresion.py"), raw, expr, "132", "1.9"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", expr, "-af", FX, "-ar", "44100",
                    os.path.join(outdir, "voz.wav")], check=True)
    json.dump({"frases": lista, "duracion": t}, open(os.path.join(outdir, "tiempos.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(lista)} frases, {t/60:.2f} min")


if __name__ == "__main__":
    main()
