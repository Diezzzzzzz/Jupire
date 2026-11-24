#!/usr/bin/env python3
"""Semis procédural de la forêt à partir du MNT (doc 31 : la végétation se re-dérive du relief).

Chaîne : DEM -> pente / exposition / écoulement -> classes de végétation -> semis Poisson-disc.
Zéro dépendance : stdlib seulement.

Entrée  : data/dem.json
Sortie  : data/world.json  (relief + classes de sol + positions d'arbres)
"""
import json, math, os, heapq, random

HERE = os.path.dirname(__file__)
DEM_IN = os.path.join(HERE, "..", "data", "dem.json")
OUT    = os.path.join(HERE, "..", "data", "world.json")

random.seed(1789)          # déterministe : même graine -> même forêt (doc 30)

# --- classes de sol ---------------------------------------------------------
EAU, ROCHER, RIPISYLVE, CHENE_VERT, CHENE_PUB, GARRIGUE, PELOUSE = range(7)
NOMS = ["eau", "rocher", "ripisylve", "chene_vert", "chene_pubescent", "garrigue", "pelouse"]

# densité *visuelle* en sprites/hectare (un sprite AoE2 = un bouquet, pas un arbre)
DENSITE = {RIPISYLVE: 85, CHENE_VERT: 70, CHENE_PUB: 60, GARRIGUE: 12,
           PELOUSE: 2, ROCHER: 45, EAU: 0}     # rocher : surtout des blocs, pas des arbres

# essences tirées par classe : (essence, poids)
ESSENCES = {
    RIPISYLVE:  [("aulne", .4), ("frene", .35), ("saule", .25)],
    CHENE_VERT: [("chene_vert", .8), ("genevrier", .2)],
    CHENE_PUB:  [("chene_pubescent", .75), ("erable", .15), ("pin", .10)],
    GARRIGUE:   [("buis", .35), ("bloc", .3), ("genevrier", .2), ("chene_vert", .15)],
    PELOUSE:    [("buis", .5), ("bloc", .2), ("chene_vert", .3)],
    # la paroi : surtout des blocs détachés (le « désordre » du doc 32) et quelques
    # pins accrochés. C'est l'éboulis qui donne son caractère à la falaise.
    ROCHER:     [("bloc", .82), ("pin", .12), ("genevrier", .06)],
}


def charger():
    with open(DEM_IN) as f:
        d = json.load(f)
    return d, d["w"], d["h"], d["step_m"], d["z"]


# --- 1. remplissage des cuvettes (priority-flood) ---------------------------
def remplir_cuvettes(z, w, h):
    """Sans ça, l'écoulement se bloque dans les artefacts d'interpolation (doc 35)."""
    out = [float("inf")] * (w * h)
    pq = []
    for j in range(h):
        for i in (0, w - 1):
            k = j * w + i
            out[k] = z[k]; heapq.heappush(pq, (z[k], k))
    for i in range(w):
        for j in (0, h - 1):
            k = j * w + i
            if out[k] == float("inf"):
                out[k] = z[k]; heapq.heappush(pq, (z[k], k))
    eps = 0.001
    while pq:
        zc, k = heapq.heappop(pq)
        if zc > out[k]:
            continue
        j, i = divmod(k, w)
        for dj, di in ((-1,0),(1,0),(0,-1),(0,1)):
            nj, ni = j + dj, i + di
            if 0 <= nj < h and 0 <= ni < w:
                nk = nj * w + ni
                if out[nk] == float("inf"):
                    out[nk] = max(z[nk], zc + eps)
                    heapq.heappush(pq, (out[nk], nk))
    return out


# --- 2. pente et exposition -------------------------------------------------
def pente_expo(z, w, h, step):
    """Retourne (pente en degrés, chaleur 0..1) — chaleur = 1 plein sud, 0 plein nord."""
    pente = [0.0] * (w * h)
    chaleur = [0.5] * (w * h)
    for j in range(h):
        for i in range(w):
            k = j * w + i
            i0, i1 = max(i-1, 0), min(i+1, w-1)
            j0, j1 = max(j-1, 0), min(j+1, h-1)
            dzdx = (z[j*w+i1] - z[j*w+i0]) / ((i1-i0) * step or step)
            # j croît vers le sud : dz/dy positif = ça monte vers le sud
            dzdy = (z[j1*w+i] - z[j0*w+i]) / ((j1-j0) * step or step)
            pente[k] = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
            # normale au versant : la pente descend dans la direction (-dzdx, -dzdy)
            # exposition sud = descend vers le sud = dzdy < 0 ... en repère image, sud = +j
            norme = math.hypot(dzdx, dzdy)
            if norme > 1e-6:
                # composante « vers le sud » du vecteur de plus grande pente descendante
                sud = -dzdy / norme          # +1 = versant exposé plein sud
                chaleur[k] = (sud + 1) / 2
            # pondéré par la raideur : un plat n'est ni adret ni ubac
            f = min(norme * 3, 1.0)
            chaleur[k] = 0.5 + (chaleur[k] - 0.5) * f
    return pente, chaleur


# --- 3. accumulation d'écoulement (D8) --------------------------------------
def accumulation(zf, w, h, step):
    ordre = sorted(range(w * h), key=lambda k: -zf[k])
    acc = [1.0] * (w * h)
    for k in ordre:
        j, i = divmod(k, w)
        best, bz = -1, zf[k]
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                if dj == di == 0:
                    continue
                nj, ni = j + dj, i + di
                if 0 <= nj < h and 0 <= ni < w:
                    nk = nj * w + ni
                    d = math.hypot(dj, di)
                    pente_v = (zf[k] - zf[nk]) / (d * step)
                    if zf[nk] < bz and pente_v > 0:
                        bz, best = zf[nk], nk
        if best >= 0:
            acc[best] += acc[k]
    return acc


# --- 4. classification ------------------------------------------------------
def classer(w, h, step, z, pente, chaleur, acc):
    cell_ha = (step * step) / 10_000.0
    zmin = min(z)
    seuil_riviere = 900        # cellules drainées -> c'est l'Ardèche
    seuil_vallon  = 90         # petit talweg
    classes = [PELOUSE] * (w * h)
    for k in range(w * h):
        a, p, c = acc[k], pente[k], chaleur[k]
        # TWI : humide si beaucoup d'eau arrive et que ça ne s'écoule pas vite
        twi = math.log((a * cell_ha * 10_000) / max(math.tan(math.radians(max(p, .6))), .01))

        if a > seuil_riviere and p < 8 and z[k] < zmin + 12:
            classes[k] = EAU
        elif p > 52:
            classes[k] = ROCHER
        elif a > seuil_vallon and twi > 11.5:
            classes[k] = RIPISYLVE
        elif c > 0.62 and p > 22:
            classes[k] = GARRIGUE          # adret raide et maigre
        elif c > 0.52:
            classes[k] = CHENE_VERT        # adret : l'yeuse
        elif c < 0.44:
            classes[k] = CHENE_PUB         # ubac frais
        else:
            classes[k] = CHENE_VERT if twi < 10.5 else CHENE_PUB
    return classes


# --- 5. semis Poisson-disc à rayon variable ---------------------------------
def semis(classes, z, w, h, step):
    """Bridson à rayon variable : le rayon découle de la densité de la classe."""
    W, H = (w - 1) * step, (h - 1) * step        # la zone n'est pas forcément carrée
    rayons = {}
    for cl, d in DENSITE.items():
        rayons[cl] = math.sqrt(10_000.0 / d / math.pi) if d > 0 else 1e9

    def classe_en(x, y):
        i = min(max(int(x / step), 0), w - 1)
        j = min(max(int(y / step), 0), h - 1)
        return classes[j * w + i]

    def alt_en(x, y):
        fx, fy = x / step, y / step
        i, j = min(int(fx), w - 2), min(int(fy), h - 2)
        u, v = fx - i, fy - j
        a, b = z[j*w+i], z[j*w+i+1]
        c, d = z[(j+1)*w+i], z[(j+1)*w+i+1]
        return (a*(1-u)+b*u)*(1-v) + (c*(1-u)+d*u)*v

    cell = 4.0                                   # grille d'accélération
    gw = int(W / cell) + 1
    grille = {}

    def libre(x, y, r):
        gx, gy = int(x / cell), int(y / cell)
        port = int(r / cell) + 1
        for j in range(gy - port, gy + port + 1):
            for i in range(gx - port, gx + port + 1):
                for (px, py, pr) in grille.get((i, j), ()):
                    if (px-x)**2 + (py-y)**2 < max(r, pr) ** 2:
                        return False
        return True

    arbres = []
    # semis par dards : on tire des candidats, on garde ce qui respecte la distance
    essais = int(W * H / 6)
    for _ in range(essais):
        x, y = random.uniform(0, W), random.uniform(0, H)
        cl = classe_en(x, y)
        if cl == EAU:
            continue
        r = rayons[cl] * random.uniform(0.85, 1.25)
        if not libre(x, y, r):
            continue
        grille.setdefault((int(x/cell), int(y/cell)), []).append((x, y, r))

        pool = ESSENCES[cl]
        t = random.random(); acc_ = 0
        essence = pool[-1][0]
        for nom, pds in pool:
            acc_ += pds
            if t <= acc_:
                essence = nom; break
        taille = random.uniform(0.75, 1.35)
        if cl == GARRIGUE:
            taille *= 0.55
        if cl == ROCHER:
            taille *= 0.7
        arbres.append([round(x, 1), round(y, 1), round(alt_en(x, y), 1),
                       essence, round(taille, 2), random.randint(0, 3)])
    return arbres


def main():
    d, w, h, step, z = charger()
    print(f"MNT {w}x{h} · pas {step} m · dénivelé {max(z)-min(z):.0f} m")

    zf = remplir_cuvettes(z, w, h)
    pente, chaleur = pente_expo(z, w, h, step)
    acc = accumulation(zf, w, h, step)
    classes = classer(w, h, step, z, pente, chaleur, acc)

    rep = {}
    for c in classes:
        rep[c] = rep.get(c, 0) + 1
    print("classes :", ", ".join(f"{NOMS[c]} {100*n/len(classes):.0f}%"
                                 for c, n in sorted(rep.items(), key=lambda x: -x[1])))
    print(f"pente : médiane {sorted(pente)[len(pente)//2]:.0f}° · max {max(pente):.0f}°")

    arbres = semis(classes, z, w, h, step)
    print(f"{len(arbres)} sprites semés "
          f"({len(arbres)/((w*step/100)*(h*step/100)):.0f}/ha)")

    with open(OUT, "w") as f:
        json.dump({"w": w, "h": h, "step_m": step, "z": z,
                   # on propage l'emprise : sans elle, impossible de savoir à quels
                   # calques (ortho, hydro) ce monde correspond — et un masque décalé
                   # plaque la rivière n'importe où
                   "lat_top": d.get("lat_top"), "lon_left": d.get("lon_left"),
                   "source": d.get("source"),
                   "classes": classes, "noms": NOMS, "arbres": arbres}, f)
    print("→", OUT, f"({os.path.getsize(OUT)/1e6:.1f} Mo)")


if __name__ == "__main__":
    main()
