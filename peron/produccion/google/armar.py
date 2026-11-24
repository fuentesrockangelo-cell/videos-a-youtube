"""Arma la voz de los cortos con frases del audio real del largo + el cierre imitado."""
import json, sys, numpy as np, soundfile as sf
S = sys.argv[1]
SR = 44100
def cargar(f):
    a, sr = sf.read(f)
    if a.ndim > 1: a = a.mean(1)
    if sr != SR:
        import librosa; a = librosa.resample(a, orig_sr=sr, target_sr=SR)
    return a
largo = cargar(f"{S}/google/largo.wav")
T = json.load(open(f"{S}/google/tiempos.json"))["frases"]
def buscar(texto, desde=0):
    for i in range(desde, len(T)):
        if T[i]["texto"].startswith(texto): return i
    raise SystemExit("no encontrada: " + texto)
def armar(frases, cta_wav, cta_json, salida):
    audio, lista, t, desde = [], [], 0.0, 0
    for txt in frases:
        i = buscar("Un comisario baleado") - 1 if txt == "Un juez muerto." else buscar(txt)
        f = T[i]
        a = largo[int(max(0, f["ini"] - 0.04) * SR): int((f["fin"] + 0.12) * SR)]
        lista.append(dict(texto=f["texto"], fin_parrafo=True, ini=t + 0.04, fin=t + len(a) / SR - 0.12))
        audio += [a, np.zeros(int(0.38 * SR))]; t += len(a) / SR + 0.38
    c = cargar(cta_wav); cj = json.load(open(cta_json))["frases"]
    for f in cj:
        lista.append(dict(texto=f["texto"], fin_parrafo=f["fin_parrafo"], ini=t + f["ini"], fin=t + f["fin"]))
    # nivel del cierre igual al del audio real
    rms = lambda x: np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2))
    c = c * rms(np.concatenate(audio)) / rms(c)
    audio.append(c); t += len(c) / SR
    a = np.concatenate(audio); a = a / np.abs(a).max() * 0.79
    import os; os.makedirs(salida, exist_ok=True)
    sf.write(f"{salida}/voz.wav", a, SR)
    json.dump({"frases": lista, "duracion": t}, open(f"{salida}/tiempos.json", "w"), ensure_ascii=False, indent=1)
    print(salida, len(lista), "frases", round(t, 1), "s")
P1 = ["Abren el ataúd", "y le faltan las manos", "Y lo más raro no es el robo", "Lo más raro es lo que les pasó",
      "Te llamas Juan Domingo Perón", "Ahí te protegen como a nadie", "Tu ataúd queda bajo un vidrio blindado",
      "Nadie podría tocarte", "Eso creían", "Pasan trece años", "Y una noche, alguien entra a tu bóveda",
      "Según los peritos", "Entonces meten las herramientas", "Y con una sierra", "te cortan las dos manos",
      "Se llevan también tu sable", "Pocos días después, llegan cartas", "Piden ocho millones de dólares",
      "Pero dentro de cada carta", "Un trozo de papel", "Es parte de una carta", "Nadie podía tener ese papel",
      "Y entonces, empieza lo peor"]
P2 = ["Un juez muerto. Un comisario baleado", "Un comisario baleado", "Un testigo asesinado",
      "Primero, un comisario que seguía la pista", "Unos desconocidos entran a su casa", "Le disparan en la cabeza",
      "Sobrevive de milagro", "Después, el sereno del cementerio", "Se llamaba Paulino Lavagno",
      "Había dicho que lo querían matar", "Poco después, lo encuentran muerto", "Y en noviembre de mil novecientos ochenta y ocho",
      "El peritaje de ese accidente", "¿Para qué alguien querría las manos de un muerto?", "Primera teoría",
      "Hay quien dice que tus manos", "Y nunca se ha probado", "Y la tercera teoría", "Una logia secreta italiana",
      "Unos periodistas aseguran", "Las manos nunca aparecieron", "Nadie fue condenado", "Y los ocho millones de dólares"]
armar(P1, f"{S}/cta/cta1-imit.wav", f"{S}/cta/cta1-tiempos.json", f"{S}/out/g-parte1")
P2[0] = "Un juez muerto."
armar(P2, f"{S}/cta/cta2-imit.wav", f"{S}/cta/cta2-tiempos.json", f"{S}/out/g-final")
# largo: audio real completo
a = cargar(f"{S}/google/largo.wav"); a = a / np.abs(a).max() * 0.79
import os; os.makedirs(f"{S}/out/g-largo", exist_ok=True)
sf.write(f"{S}/out/g-largo/voz.wav", a, SR)
d = json.load(open(f"{S}/google/tiempos.json")); json.dump(d, open(f"{S}/out/g-largo/tiempos.json", "w"), ensure_ascii=False, indent=1)
print("largo", round(d["duracion"], 1), "s")
