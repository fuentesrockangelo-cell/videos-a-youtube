"""Genera la voz en off de un guion y los tiempos de cada frase.

Uso: KOKORO_DIR=... python3 voz.py guion.txt salida_dir
Produce salida_dir/voz.wav y salida_dir/tiempos.json

Voz natural: Kokoro genera cada PÁRRAFO entero (la entonación fluye entre frases, como una persona)
y los tiempos de cada frase se recuperan buscando las pausas dentro del párrafo.
Procesado mínimo: sin eco corto ni cambios de tono, que son lo que hace sonar robótica una voz.

Variables:
  KOKORO_DIR   carpeta kokoro-multi-lang-v1_0
  KOKORO_VOZ   29 = em_alex, 53 = em_santa (hombres, español)
  VOZ_VEL      velocidad base (1.0 = normal)
  VOZ_CALIDEZ  dB de graves cálidos (150 Hz), por defecto 1.5
  PIPER_MODEL  alternativa antigua (piper), solo si no hay KOKORO_DIR
"""
import json, os, re, subprocess, sys, wave
import numpy as np

KOKORO = os.environ.get("KOKORO_DIR")
KOKORO_VOZ = int(os.environ.get("KOKORO_VOZ", "29"))
MODEL = os.environ.get("PIPER_MODEL")
SR = 24000
PAUSA_PARRAFO = 0.65


def fx_natural():
    """Solo ecualización suave: sin compresor ni loudnorm (aplastan la voz y la saturan)."""
    cal = float(os.environ.get("VOZ_CALIDEZ", "2.5"))
    return (f"highpass=f=60,equalizer=f=150:t=q:w=1:g={cal},equalizer=f=3000:t=q:w=1.5:g=-1.5,"
            "highshelf=f=6000:g=-4.5")


def dinamica(a, lista, sr):
    """Volumen por frase como un narrador: suspenso más bajo, golpes cortos más fuertes."""
    g = np.ones_like(a)
    for f in lista:
        t = f["texto"].lower(); n = len(t.split())
        db = -2.5 if t.endswith("...") else 2.0 if n <= 5 else 1.0 if t.endswith("?") else 0.0
        g[int(f["ini"] * sr): int(f["fin"] * sr)] = 10 ** (db / 20)
    k = int(0.06 * sr)
    return a * np.convolve(g, np.ones(k) / k, mode="same")


def parrafos(texto):
    out = []
    for p in [p.strip() for p in texto.split("\n\n") if p.strip()]:
        partes = re.findall(r'[^.?!…]+(?:\.\.\.|[.?!…])*"?', p.replace("\n", " "))
        out.append([s.strip() for s in partes if s.strip()])
    return out


def velocidad(frases):
    """Párrafos de suspenso un poco más lentos; el resto a ritmo natural."""
    base = float(os.environ.get("VOZ_VEL", "1.0"))
    t = " ".join(frases).lower()
    if "..." in t:
        return base * 0.94
    if len(frases) == 1 and len(t.split()) <= 6:
        return base * 0.96
    return base


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
        return lambda texto, vel: np.asarray(tts.generate(texto, sid=KOKORO_VOZ, speed=vel).samples, dtype=np.float32)
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(MODEL)
    SR = voice.config.sample_rate
    return lambda texto, vel: np.concatenate([c.audio_float_array for c in voice.synthesize(
        texto, syn_config=SynthesisConfig(length_scale=1.0 / vel))])


def cortes(a, n):
    """Devuelve n-1 puntos de corte entre frases: las n-1 pausas más largas del párrafo."""
    if n <= 1:
        return []
    hop = int(0.01 * SR)
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    umbral = max(0.008, np.percentile(e, 20) * 1.5)
    silencio = e < umbral
    runs, i = [], 0
    while i < len(silencio):
        if silencio[i]:
            j = i
            while j < len(silencio) and silencio[j]:
                j += 1
            if i > 0 and j < len(silencio):
                runs.append((j - i, (i + j) // 2))
            i = j
        else:
            i += 1
    runs = sorted(runs, reverse=True)[:n - 1]
    pts = sorted(c * hop for _, c in runs)
    if len(pts) < n - 1:  # si faltan pausas, reparte por longitud
        pts = [int(len(a) * (k + 1) / n) for k in range(n - 1)]
    return pts


def main():
    guion, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    say = sintetizador()
    lista, audio, t = [], [], 0.0
    for frs in parrafos(open(guion, encoding="utf-8").read()):
        a = say(" ".join(frs).replace('"', ""), velocidad(frs))
        nz = np.where(np.abs(a) > 0.01)[0]
        if len(nz):
            a = a[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.1 * SR)]
        pts = [0] + cortes(a, len(frs)) + [len(a)]
        for k, fr in enumerate(frs):
            lista.append({"texto": fr, "fin_parrafo": k == len(frs) - 1,
                          "ini": t + pts[k] / SR, "fin": t + pts[k + 1] / SR})
        audio.append(a)
        t += len(a) / SR
        audio.append(np.zeros(int(PAUSA_PARRAFO * SR), dtype=np.float32))
        t += PAUSA_PARRAFO
    a = dinamica(np.concatenate(audio), lista, SR)
    a = (a / max(1e-6, np.abs(a).max()) * 0.79 * 32767).astype(np.int16)  # pico a -2 dB, sin recortes
    raw = os.path.join(outdir, "voz_cruda.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", fx_natural(), "-ar", "44100",
                    os.path.join(outdir, "voz.wav")], check=True)
    json.dump({"frases": lista, "duracion": t}, open(os.path.join(outdir, "tiempos.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(lista)} frases, {t/60:.2f} min")


if __name__ == "__main__":
    main()
