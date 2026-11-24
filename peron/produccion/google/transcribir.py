"""Corta el audio real en sus pausas, transcribe cada trozo con Whisper y empareja con el guion."""
import json, re, sys, subprocess, difflib, unicodedata
import numpy as np, soundfile as sf, sherpa_onnx
from num2words import num2words
guion_json, real_wav, out_json, wdir = sys.argv[1:5]
a, sr = sf.read(real_wav)
dur = len(a) / sr
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", real_wav, "-af", "silencedetect=n=-38dB:d=0.12", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
# trozos de voz entre pausas
bordes = []; t = 0.0
for s, e in zip(st, en + [dur]):
    if s - t > 0.08: bordes.append((t, s))
    t = e
if dur - t > 0.08: bordes.append((t, dur))
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{wdir}/small-encoder.int8.onnx", decoder=f"{wdir}/small-decoder.int8.onnx",
    tokens=f"{wdir}/small-tokens.txt", language="es", task="transcribe", num_threads=8)
def norm(w):
    w = unicodedata.normalize("NFD", w.lower()); w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", w)
def palabras(txt):
    out = []
    for w in txt.split():
        n = norm(w)
        if n.isdigit():
            out += [norm(x) for x in num2words(int(n), lang="es").split()]
        elif n:
            out.append(n)
    return out
asr = []  # (palabra, idx_trozo)
trozos = []
for k, (i0, i1) in enumerate(bordes):
    seg = a[int(i0 * sr): int(i1 * sr)].astype(np.float32)
    s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
    txt = s.result.text.strip(); trozos.append(dict(ini=i0, fin=i1, texto=txt))
    asr += [(w, k) for w in palabras(txt)]
d = json.load(open(guion_json)); fr = d["frases"]
guion = []  # (palabra, idx_frase)
for i, f in enumerate(fr):
    guion += [(w, i) for w in palabras(f["texto"])]
sm = difflib.SequenceMatcher(None, [w for w, _ in guion], [w for w, _ in asr], autojunk=False)
g2t = {}
for blk in sm.get_matching_blocks():
    for q in range(blk.size):
        g2t[blk.a + q] = asr[blk.b + q][1]
out = []
for i, f in enumerate(fr):
    idx = [g for g, (_, fi) in enumerate(guion) if fi == i]
    ks = [g2t[g] for g in idx if g in g2t]
    out.append(dict(texto=f["texto"], fin_parrafo=f["fin_parrafo"],
                    ini=trozos[min(ks)]["ini"] if ks else None, fin=trozos[max(ks)]["fin"] if ks else None,
                    match=len(ks) / max(1, len(idx))))
# rellena frases sin coincidencias interpolando
for i, o in enumerate(out):
    if o["ini"] is None:
        p = next((out[j]["fin"] for j in range(i - 1, -1, -1) if out[j]["fin"] is not None), 0.0)
        nx = next((out[j]["ini"] for j in range(i + 1, len(out)) if out[j]["ini"] is not None), dur)
        o["ini"], o["fin"] = p + 0.05, nx - 0.05
for i in range(1, len(out)):
    if out[i]["ini"] < out[i - 1]["fin"]:
        out[i]["ini"] = out[i - 1]["fin"]
json.dump({"frases": out, "duracion": dur}, open(out_json, "w"), ensure_ascii=False, indent=1)
json.dump(trozos, open(out_json.replace(".json", "_trozos.json"), "w"), ensure_ascii=False, indent=1)
m = [o["match"] for o in out]
print(f"{len(bordes)} trozos; frases con coincidencia: {sum(x > 0 for x in m)}/{len(m)}; media de palabras emparejadas {np.mean(m)*100:.0f}%")
