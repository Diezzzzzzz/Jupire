#!/usr/bin/env python3
"""Extrait 480 x 480 m du MNT LiDAR de Balazuc, rééchantillonné à 1 m,
et l'écrit dans donnees-falaise.js pour falaise-cellules.html.

Python pur (ni numpy ni Pillow sur cette machine).
    python3 proto-da/generer_falaise.py
"""
import base64, json, math, os, struct

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
COTE_M = 480            # côté de l'extrait, en mètres
N = COTE_M + 1          # échantillons (coins de cellules de 1 m)
ORIGINE_I, ORIGINE_J = 416, 672   # coin nord-ouest dans dem.json (échantillons)

d = json.load(open(os.path.join(RACINE, "proto-terrain/data/dem.json")))
w, pas, z = d["w"], d["step_m"], d["z"]
eau = struct.unpack("<%df" % (1024 * 1024),
                    open(os.path.join(RACINE, "proto-godot/data/eau.bin"), "rb").read())


def alt(x, y):
    """Altitude bilinéaire à (x, y) mètres du coin de l'extrait."""
    fi = ORIGINE_I + x / pas
    fj = ORIGINE_J + y / pas
    i, j = int(fi), int(fj)
    a, b = fi - i, fj - j
    r = j * w + i
    return ((z[r] * (1 - a) + z[r + 1] * a) * (1 - b)
            + (z[r + w] * (1 - a) + z[r + w + 1] * a) * b)


H = [[alt(i, j) for i in range(N)] for j in range(N)]
zmin = min(min(l) for l in H)
zmax = max(max(l) for l in H)

# Masque d'eau : eau.bin est à 2,344 m sur la même emprise, NAN hors rivière.
def est_eau(x, y):
    ei = int((ORIGINE_I + x / pas) / 2)
    ej = int((ORIGINE_J + y / pas) / 2)
    v = eau[ej * 1024 + ei]
    return v == v

E = [[1 if est_eau(i, j) else 0 for i in range(N)] for j in range(N)]

# Pente à 1 m (différences centrées).
def pente(i, j):
    i0, i1 = max(i - 1, 0), min(i + 1, N - 1)
    j0, j1 = max(j - 1, 0), min(j + 1, N - 1)
    gx = (H[j][i1] - H[j][i0]) / (i1 - i0)
    gy = (H[j1][i] - H[j0][i]) / (j1 - j0)
    return gx, gy

# Rotation par défaut : celle où le plus de parois regardent la caméra.
# Même convention que la page : un quart de tour envoie (vx, vy) sur (-vy, vx),
# et la caméra est du côté (+1, +1).
faces = [0, 0, 0, 0]
for j in range(0, N, 2):
    for i in range(0, N, 2):
        gx, gy = pente(i, j)
        if gx * gx + gy * gy < 1.0:      # moins de 45°
            continue
        vx, vy = -gx, -gy                # sens de la descente
        for r in range(4):
            if vx + vy > 0:
                faces[r] += 1
            vx, vy = -vy, vx
rot = max(range(4), key=lambda r: faces[r])

# Repères d'échelle : une maison sur un replat près d'un haut de paroi,
# un personnage à côté, un autre sur la berge.
def plat(i, j, r=7):
    mn = 1e9; mx = -1e9
    for b in range(j - r, j + r + 1, 2):
        for a in range(i - r, i + r + 1, 2):
            if E[b][a]:
                return 99
            v = H[b][a]
            mn = min(mn, v); mx = max(mx, v)
    return mx - mn

raides = [(i, j) for j in range(20, N - 20, 3) for i in range(20, N - 20, 3)
          if sum(g * g for g in pente(i, j)) > 3.0]          # plus de 60°
maison = None
berge = None
meilleur = 1e9
for j in range(40, N - 40, 4):
    for i in range(40, N - 40, 4):
        p = plat(i, j)
        if p > 1.6:
            continue
        haut = H[j][i] - zmin
        dparoi = min(math.hypot(i - a, j - b) for a, b in raides)
        centre = math.hypot(i - N / 2, j - N / 2)
        if haut > 30 and 12 < dparoi < 30:
            note = centre
            if note < meilleur:
                meilleur = note; maison = (i, j)
meilleur = 1e9
for j in range(40, N - 40, 3):
    for i in range(40, N - 40, 3):
        if plat(i, j, 3) > 1.2:
            continue
        deau = min((math.hypot(a, b) for a in range(-12, 13, 3) for b in range(-12, 13, 3)
                    if E[j + b][i + a]), default=99)
        if 4 < deau < 12:
            note = math.hypot(i - N / 2, j - N / 2)
            if note < meilleur:
                meilleur = note; berge = (i, j)

brut = b"".join(struct.pack("<%dH" % N, *[int(round((v - zmin) * 100)) for v in l]) for l in H)
bits = bytearray((N * N + 7) // 8)
for j in range(N):
    for i in range(N):
        if E[j][i]:
            k = j * N + i
            bits[k >> 3] |= 1 << (k & 7)

sortie = {
    "n": N, "cote_m": COTE_M, "zmin": round(zmin, 2), "zmax": round(zmax, 2),
    "rotation_defaut": rot, "parois_face_camera": faces,
    "maison": maison, "berge": berge,
    "lat_nord": round(d["lat_top"] - ORIGINE_J * pas / 111320, 5),
    "lon_ouest": round(d["lon_left"] + ORIGINE_I * pas / (111320 * math.cos(math.radians(d["lat_top"]))), 5),
    "source": "IGN LiDAR HD, MNT 1,172 m rééchantillonné à 1 m (proto-terrain/data/dem.json)",
    "alt_cm_u16": base64.b64encode(brut).decode(),
    "eau_bits": base64.b64encode(bytes(bits)).decode(),
}
with open(os.path.join(ICI, "donnees-falaise.js"), "w") as f:
    f.write("window.DONNEES = " + json.dumps(sortie) + ";\n")
print({k: v for k, v in sortie.items() if not k.endswith(("u16", "bits"))})
print("eau :", sum(map(sum, E)), "cellules ; parois > 60° :", len(raides) * 9)

# Semis d'arbres du proto Godot (positions réelles tirées du LiDAR), restreint à l'extrait.
# arbres.bin : n x (float32 x, float32 z, uint8 espèce, float32 échelle, uint8 variante), mètres depuis le coin NO de l'emprise.
ab = open(os.path.join(RACINE, "proto-godot/data/arbres.bin"), "rb").read()
x0, y0 = ORIGINE_I * pas, ORIGINE_J * pas
arbres = []
for t in range(len(ab) // 14):
    x, y, esp, ech, var = struct.unpack_from("<ffBfB", ab, t * 14)
    x -= x0; y -= y0
    if 2 <= x <= COTE_M - 2 and 2 <= y <= COTE_M - 2 and not E[int(round(y))][int(round(x))]:
        arbres += [int(round(x * 10)), int(round(y * 10)), esp, int(round(ech * 100)), var]
with open(os.path.join(ICI, "donnees-arbres.js"), "w") as f:
    f.write("// x, y en décimètres ; espèce (0 arbuste, 3 chêne vert, 4 chêne pubescent) ; échelle en % ; variante\n")
    f.write("window.ARBRES = " + json.dumps(arbres, separators=(",", ":")) + ";\n")
print("arbres dans l'extrait :", len(arbres) // 5)
