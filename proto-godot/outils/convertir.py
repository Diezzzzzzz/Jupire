#!/usr/bin/env python3
"""
world_NNNN.json + world_NNNN.hydro.png  →  binaires prêts à rendre, pour Godot.

Principe : Godot ne doit RIEN calculer du monde. Tout le travail de terrain
(débruitage, aplatissement, creusement des gorges, couture des berges, surface
d'eau, filtrage du semis, couleurs) se fait ici, une fois, en Python pur —
comme le reste du pipeline Jupire. Godot charge des tableaux et les affiche.

    python3 outils/convertir.py [source.json] [facteur]

Réglages : ceux validés dans proto-terrain/PROMPT-REPRISE.md (lissage 5 m,
aplatissement 0,85, creusement ×1,1, eau +0,5 m). Cf. NOTE sur le lissage.

Sorties dans data/ :
    terrain.bin   float32 LE, n*n altitudes transformées (m), nord→sud
    couleurs.bin  uint8, n*n*3, teinte de classe + ombrage
    eau.bin       float32, n*n : altitude de la surface d'eau, NAN hors rivière
    arbres.bin    n × (float32 x, float32 z, uint8 espece, float32 echelle)
                  DÉJÀ filtré du masque d'eau + marge de berge
    monde.json    métadonnées
"""

import json, math, os, struct, sys, time, zlib

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    RACINE, "..", "proto-terrain", "data", "world_2400.json")
FACT = int(sys.argv[2]) if len(sys.argv) > 2 else 2   # 2048 → 1024, pas 2,344 m

# ── réglages validés (PROMPT-REPRISE.md) ───────────────────────────────────
LISSAGE   = 5.0    # m — NOTE : l'original applique un filtre bilatéral, qui
                   # préserve l'arête de falaise. Ici, gaussienne sur une grille
                   # déjà moyennée 2×2 : le grain LiDAR est déjà à moitié parti,
                   # mais les crêtes sont un cheveu plus rondes. À juger à l'œil.
APLATIR   = 0.85   # k : compression des grandes formes
CREUSER   = 1.1    # gain sur le détail, dans les creux seulement
EAU_OFF   = 0.5    # m au-dessus du niveau détecté
MARGE_BERGE = 6.0  # m : aucun arbre à moins de ça de l'eau (le bug 2)

SOL_AZ, SOL_EL = 2.35, 0.42        # soleil, mêmes valeurs que le proto browser

# Deux lumières, pas une. Le soleil est chaud, le ciel est froid : c'est ce qui
# donne des ombres BLEUES au lieu de gris, et c'est la moitié de l'effet
# « peinture » de SC4. Une seule lumière blanche rend le relief plat et terne.
COUL_SOLEIL = (1.00, 0.93, 0.76)
COUL_CIEL   = (0.56, 0.68, 0.92)
ECHELLE_LUM = 1.6      # l'éclairage dépasse 1 : on le range dans un octet

# teintes par classe : eau, rocher, ripisylve, chêne vert, chêne pubescent,
# garrigue, pelouse. Le calcaire est passé de 138 à 92 : au-dessus, une grande
# pente ensoleillée vire au champ de neige — c'est ce qu'on voyait au build g2.
TEINTES = [(60, 84, 96), (92, 86, 72), (62, 84, 54), (58, 76, 48),
           (88, 100, 56), (110, 108, 72), (132, 130, 92)]


# ── utilitaires grille ─────────────────────────────────────────────────────
def flou(src, n, pas, sigma):
    """Gaussienne séparable, bords répliqués."""
    if sigma <= 0:
        return list(src)
    s = sigma / pas
    r = max(1, int(round(s * 2.5)))
    noy = [math.exp(-(i * i) / (2 * s * s)) for i in range(-r, r + 1)]
    som = sum(noy)
    noy = [v / som for v in noy]
    t = [0.0] * (n * n)
    o = [0.0] * (n * n)
    for j in range(n):
        b = j * n
        for i in range(n):
            v = 0.0
            for k in range(-r, r + 1):
                ii = i + k
                if ii < 0: ii = 0
                elif ii >= n: ii = n - 1
                v += src[b + ii] * noy[k + r]
            t[b + i] = v
    for j in range(n):
        for i in range(n):
            v = 0.0
            for k in range(-r, r + 1):
                jj = j + k
                if jj < 0: jj = 0
                elif jj >= n: jj = n - 1
                v += t[jj * n + i] * noy[k + r]
            o[j * n + i] = v
    return o


def flou_large(src, n, pas, sigma):
    """Gaussienne très large : on décime, on floute petit, on ré-interpole.
    Sans ça, un sigma de 250 m coûterait un noyau de 200 taps."""
    f = max(1, int(round(sigma / (pas * 12))))
    if f == 1:
        return flou(src, n, pas, sigma)
    d = (n + f - 1) // f
    petit = [0.0] * (d * d)
    for j in range(d):
        for i in range(d):
            s = 0.0; c = 0
            for b in range(f):
                jj = j * f + b
                if jj >= n: break
                row = jj * n
                for a in range(f):
                    ii = i * f + a
                    if ii >= n: break
                    s += src[row + ii]; c += 1
            petit[j * d + i] = s / c
    petit = flou(petit, d, pas * f, sigma)
    out = [0.0] * (n * n)
    for j in range(n):
        fy = min(j / f, d - 1.001)
        jj = int(fy); v = fy - jj
        for i in range(n):
            fx = min(i / f, d - 1.001)
            ii = int(fx); u = fx - ii
            a = petit[jj * d + ii]; b = petit[jj * d + ii + 1]
            c = petit[(jj + 1) * d + ii]; e = petit[(jj + 1) * d + ii + 1]
            out[j * n + i] = (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + e * u) * v
    return out


def dilate(masque, n, pas, rayon_m):
    """Dilatation carrée (séparable) d'un masque 0/1."""
    r = max(1, int(round(rayon_m / pas)))
    t = bytearray(n * n)
    for j in range(n):
        b = j * n
        for i in range(n):
            if masque[b + i]:
                for k in range(max(0, i - r), min(n, i + r + 1)):
                    t[b + k] = 1
    o = bytearray(n * n)
    for j in range(n):
        for i in range(n):
            if t[j * n + i]:
                for k in range(max(0, j - r), min(n, j + r + 1)):
                    o[k * n + i] = 1
    return o


def reduire(src, n, f):
    """Moyenne de boîte n×n → d×d, pour calculer l'éclairage moins cher."""
    d = n // f
    out = [0.0] * (d * d)
    inv = 1.0 / (f * f)
    for j in range(d):
        base = j * f * n
        for i in range(d):
            b = base + i * f
            s = 0.0
            for dj in range(f):
                r = b + dj * n
                for di in range(f):
                    s += src[r + di]
            out[j * d + i] = s * inv
    return out, d


def agrandir(src, d, n):
    """Bilinéaire d×d → n×n."""
    out = [0.0] * (n * n)
    e = (d - 1.0) / (n - 1.0)
    for j in range(n):
        fy = j * e
        jj = int(fy)
        if jj > d - 2: jj = d - 2
        v = fy - jj
        r0 = jj * d
        r1 = r0 + d
        for i in range(n):
            fx = i * e
            ii = int(fx)
            if ii > d - 2: ii = d - 2
            u = fx - ii
            out[j * n + i] = ((src[r0 + ii] * (1 - u) + src[r0 + ii + 1] * u) * (1 - v)
                            + (src[r1 + ii] * (1 - u) + src[r1 + ii + 1] * u) * v)
    return out


def ombre_portee(Z, n, pas, az, el, f=2):
    """1 là où le soleil est bouché par le relief.

    C'est ce qui manquait le plus : sans ombre portée, une falaise de 60 m ne
    projette rien et la gorge n'a pas de fond. L'ombre est BASSE FRÉQUENCE par
    nature (constat du proto browser), donc on la calcule sur une grille réduite
    et on la ré-interpole — invisible à l'œil, quatre fois moins cher.
    """
    Zr, d = reduire(Z, n, f)
    pr = pas * f
    dx, dz = math.sin(az), math.cos(az)
    t = math.tan(el)
    zmax = max(Zr)
    out = [0.0] * (d * d)
    for j in range(d):
        for i in range(d):
            k = j * d + i
            z = Zr[k]
            porte = (zmax - z) / t          # au-delà, plus rien ne peut boucher
            s = pr
            while s < porte:
                x = i + dx * s / pr
                y = j + dz * s / pr
                ii, jj = int(x), int(y)
                if ii < 0 or jj < 0 or ii >= d or jj >= d:
                    break
                if Zr[jj * d + ii] > z + s * t:
                    out[k] = 1.0
                    break
                s += pr
    out = flou(out, d, pr, pr * 1.2)        # bord adouci, pas d'escalier
    return agrandir(out, d, n)


def ciel_ouvert(Z, n, pas, f=4, dirs=16, portee=160.0):
    """Part de ciel visible (0 = fond de faille, 1 = sommet dégagé).

    C'est l'occlusion ambiante du relief : elle assombrit les fonds de gorge et
    fait ressortir les crêtes. Avec l'ombre portée, c'est ce qui donne le
    volume — et ça sert directement la doc 05 (le fond de gorge est clos).
    """
    Zr, d = reduire(Z, n, f)
    pr = pas * f
    pas_max = max(2, int(portee / pr))
    rayons = []
    for a in range(dirs):
        ang = 2.0 * math.pi * a / dirs
        rayons.append((math.sin(ang), math.cos(ang)))
    out = [0.0] * (d * d)
    for j in range(d):
        for i in range(d):
            k = j * d + i
            z = Zr[k]
            somme = 0.0
            for (dx, dz) in rayons:
                h = 0.0
                for s in range(1, pas_max):
                    ii = int(i + dx * s)
                    jj = int(j + dz * s)
                    if ii < 0 or jj < 0 or ii >= d or jj >= d:
                        break
                    a = (Zr[jj * d + ii] - z) / (s * pr)
                    if a > h:
                        h = a
                somme += 1.0 / math.sqrt(1.0 + h * h)   # = cos(atan(h))
            out[k] = somme / dirs
    return agrandir(out, d, n)


def bruit(n, pas, echelle=18.0):
    """Petit bruit lissé, pour que les grandes surfaces ne soient pas unies."""
    r = 1103515245
    g = [0.0] * (n * n)
    for i in range(n * n):
        r = (r * 1103515245 + 12345) & 0x7FFFFFFF
        g[i] = (r >> 8 & 1023) / 1023.0 - 0.5
    return flou(g, n, pas, echelle)


# ── PNG : décodeur minimal (RGBA 8 bits, non entrelacé) ────────────────────
def lire_png_alpha(chemin):
    b = open(chemin, "rb").read()
    assert b[:8] == b"\x89PNG\r\n\x1a\n", "pas un PNG"
    o, idat = 8, bytearray()
    w = h = ct = bd = None
    while o < len(b):
        ln, typ = struct.unpack(">I4s", b[o:o + 8])
        if typ == b"IHDR":
            w, h, bd, ct, _, _, inter = struct.unpack(">IIBBBBB", b[o + 8:o + 21])
            assert bd == 8 and inter == 0, f"PNG non géré (bd={bd}, entrelacé={inter})"
        elif typ == b"IDAT":
            idat += b[o + 8:o + 8 + ln]
        o += 12 + ln
    canaux = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    brut = zlib.decompress(bytes(idat))
    lig = w * canaux
    out = bytearray(w * h)          # on ne garde QUE l'alpha (ou le gris)
    prec = bytearray(lig)
    p = 0
    for j in range(h):
        f = brut[p]; p += 1
        cur = bytearray(brut[p:p + lig]); p += lig
        if f == 1:
            for i in range(canaux, lig):
                cur[i] = (cur[i] + cur[i - canaux]) & 255
        elif f == 2:
            for i in range(lig):
                cur[i] = (cur[i] + prec[i]) & 255
        elif f == 3:
            for i in range(lig):
                a = cur[i - canaux] if i >= canaux else 0
                cur[i] = (cur[i] + ((a + prec[i]) >> 1)) & 255
        elif f == 4:
            for i in range(lig):
                a = cur[i - canaux] if i >= canaux else 0
                c = prec[i - canaux] if i >= canaux else 0
                pa, pb, pc = abs(prec[i] - c), abs(a - c), abs(a + prec[i] - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (prec[i] if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 255
        prec = cur
        dec = canaux - 1 if ct in (4, 6) else 0     # alpha = dernier canal
        base = j * w
        for i in range(w):
            out[base + i] = cur[i * canaux + dec]
    return w, h, out


# ── programme ──────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    top = lambda m: print(f"  [{time.time()-t0:6.1f} s] {m}", flush=True)

    print(f"lecture {os.path.basename(SRC)} …", flush=True)
    d = json.load(open(SRC))
    w, h, pas0 = d["w"], d["h"], d["step_m"]
    z, cl, noms = d["z"], d["classes"], d["noms"]
    n, pas = w // FACT, pas0 * FACT
    emprise = w * pas0
    top(f"{w}×{h} au pas de {pas0:.3f} m → {n}×{n} au pas de {pas:.3f} m")

    # altitudes : moyenne de boîte (pas un point sur FACT : ça ferait clignoter
    # les arêtes de falaise d'un facteur à l'autre)
    inv = 1.0 / (FACT * FACT)
    Zb = [0.0] * (n * n)
    cls = bytearray(n * n)
    for j in range(n):
        base = j * FACT * w
        for i in range(n):
            b = base + i * FACT
            s = 0.0
            for dj in range(FACT):
                r = b + dj * w
                for di in range(FACT):
                    s += z[r + di]
            Zb[j * n + i] = s * inv
            cls[j * n + i] = cl[b]
    del z, cl
    top("rééchantillonné")

    # ── masque d'eau : BD TOPO (le semis, lui, ne voit que 0,3 % d'eau)
    png = SRC.replace(".json", ".hydro.png")
    masque = bytearray(n * n)
    if os.path.exists(png):
        pw, ph, alpha = lire_png_alpha(png)
        for j in range(n):
            sj = j * ph // n
            for i in range(n):
                if alpha[sj * pw + (i * pw // n)] > 40:
                    masque[j * n + i] = 1
        top(f"masque d'eau BD TOPO {pw}×{ph} → {100*sum(masque)/(n*n):.2f} % de l'emprise")
    else:
        print(f"  !! {os.path.basename(png)} absent : pas d'eau, pas de filtrage du semis")

    # ── champs dérivés (port de appliquer() du proto browser)
    Z0 = flou(Zb, n, pas, LISSAGE); top("débruitage")
    bf = flou_large(Z0, n, pas, 250.0); top("grandes formes (250 m)")
    ZDOUX = flou(Z0, n, pas, 7.0); top("version adoucie (berges)")

    # raideur : la pente se juge sur ~8 m, transition franche 30°→42°
    R = max(1, int(round(8 / pas)))
    raide = [0.0] * (n * n)
    for j in range(n):
        j0, j1 = max(j - R, 0), min(j + R, n - 1)
        for i in range(n):
            i0, i1 = max(i - R, 0), min(i + R, n - 1)
            dx = (Z0[j * n + i1] - Z0[j * n + i0]) / ((i1 - i0) * pas)
            dz = (Z0[j1 * n + i] - Z0[j0 * n + i]) / ((j1 - j0) * pas)
            p = (math.degrees(math.atan(math.hypot(dx, dz))) - 30) / 12
            raide[j * n + i] = 0.0 if p < 0 else (1.0 if p > 1 else p)
    # on ne creuse JAMAIS un cours d'eau ni ses berges : le gain mordait le pied
    # de berge → les crevasses signalées à la session de juillet
    bloque = dilate(masque, n, pas, 6.0)
    for i in range(n * n):
        if bloque[i]:
            raide[i] = 0.0
    raide = flou(raide, n, pas, 2.5); top("raideur")

    berge = flou([float(v) for v in dilate(masque, n, pas, 5.0)], n, pas, 4.0)
    top("couture des berges")

    # z' = k·(grandes formes) + gain·(détail), gain sur les creux seulement
    Zc = [0.0] * (n * n)
    for i in range(n * n):
        hf = Z0[i] - bf[i]
        g = 1 + (CREUSER - 1) * raide[i] * (1.0 if hf < 0 else 0.5)
        v = APLATIR * bf[i] + g * hf
        if berge[i] > 0.01:
            t = min(berge[i], 1.0) * 0.85
            v = v * (1 - t) + (APLATIR * bf[i] + (ZDOUX[i] - bf[i])) * t
        Zc[i] = v
    top(f"terrain transformé (k={APLATIR}, gain×{CREUSER})")

    # ── surface d'eau : minimum local du lit, puis lissé le long du cours.
    # Une surface d'eau est plate en travers ; sur 2,4 km de gorge elle descend.
    # Un plan unique serait faux, d'où un champ par maille.
    NAN = float("nan")
    eau = [NAN] * (n * n)
    rm = max(1, int(round(24 / pas)))
    for j in range(n):
        for i in range(n):
            if not masque[j * n + i]:
                continue
            m = 1e9
            for jj in range(max(0, j - rm), min(n, j + rm + 1)):
                b = jj * n
                for ii in range(max(0, i - rm), min(n, i + rm + 1)):
                    if masque[b + ii] and Zc[b + ii] < m:
                        m = Zc[b + ii]
            eau[j * n + i] = m + EAU_OFF
    # lissage le long du cours, restreint au masque
    tmp = [0.0 if eau[i] != eau[i] else eau[i] for i in range(n * n)]
    poids = [0.0 if eau[i] != eau[i] else 1.0 for i in range(n * n)]
    tmp = flou(tmp, n, pas, 30.0)
    poids = flou(poids, n, pas, 30.0)
    for i in range(n * n):
        if masque[i] and poids[i] > 1e-6:
            eau[i] = tmp[i] / poids[i]
    top("surface d'eau")

    # ── éclairage : soleil direct + ombre portée + part de ciel visible
    OMB = ombre_portee(Zc, n, pas, SOL_AZ, SOL_EL)
    top("ombres portées")
    SVF = ciel_ouvert(Zc, n, pas)
    top("part de ciel visible")
    BR = bruit(n, pas)
    top("bruit de surface")

    # Bandes de berge, pour la couche de galets : deux dilatations donnent une
    # transition au lieu d'un trait.
    berge_pres = dilate(masque, n, pas, 7.0)
    berge_loin = dilate(masque, n, pas, 22.0)

    lum = (math.cos(SOL_EL) * math.sin(SOL_AZ), math.sin(SOL_EL),
           math.cos(SOL_EL) * math.cos(SOL_AZ))
    coul = bytearray(n * n * 3)
    # lumiere = l'éclairage SEUL, sans teinte : c'est lui que le shader
    # multipliera par les textures tuilées. Cuit une fois, gratuit à l'écran.
    lumi = bytearray(n * n * 3)
    # couches = poids des quatre matières (falaise, garrigue, sous-bois, berge)
    couches = bytearray(n * n * 4)
    for j in range(n):
        j0, j1 = max(j - 1, 0), min(j + 1, n - 1)
        for i in range(n):
            i0, i1 = max(i - 1, 0), min(i + 1, n - 1)
            k = j * n + i
            dx = (Zc[j * n + i1] - Zc[j * n + i0]) / ((i1 - i0) * pas)
            dz = (Zc[j1 * n + i] - Zc[j0 * n + i]) / ((j1 - j0) * pas)
            ln = math.sqrt(dx * dx + dz * dz + 1.0)
            nx, ny, nz = -dx / ln, 1.0 / ln, -dz / ln
            ndl = nx * lum[0] + ny * lum[1] + nz * lum[2]
            if ndl < 0.0:
                ndl = 0.0
            # une pente peut être face au soleil ET dans l'ombre d'une falaise
            direct = 0.85 * ndl * (1.0 - OMB[k])
            ambiant = 0.08 + 0.42 * SVF[k]
            r, g, b = TEINTES[cls[k]] if not masque[k] else TEINTES[0]
            v = 1.0 + BR[k] * 0.55
            if raide[k] > 0.30 and not masque[k]:       # falaise : la roche perce
                t = min(1.0, (raide[k] - 0.30) / 0.35)
                rr, gg, bb = TEINTES[1]
                r, g, b = r + (rr - r) * t, g + (gg - g) * t, b + (bb - b) * t
                # la roche nue est bien plus bigarrée qu'un couvert végétal :
                # sans ce grain, une grande falaise devient un aplat
                v += BR[k] * 1.1 * t
            r *= v; g *= v; b *= v
            lr = ambiant * COUL_CIEL[0] + direct * COUL_SOLEIL[0]
            lg = ambiant * COUL_CIEL[1] + direct * COUL_SOLEIL[1]
            lb = ambiant * COUL_CIEL[2] + direct * COUL_SOLEIL[2]
            coul[k*3]   = max(0, min(255, int(r * lr)))
            coul[k*3+1] = max(0, min(255, int(g * lg)))
            coul[k*3+2] = max(0, min(255, int(b * lb)))
            lumi[k*3]   = max(0, min(255, int(lr / ECHELLE_LUM * 255)))
            lumi[k*3+1] = max(0, min(255, int(lg / ECHELLE_LUM * 255)))
            lumi[k*3+2] = max(0, min(255, int(lb / ECHELLE_LUM * 255)))

            # ── mélange des matières.
            # La pente commande : une falaise est nue par définition, rien n'y
            # tient. Le reste se départage entre le couvert (sous-bois) et
            # l'ouvert (garrigue), et la berge prend les galets.
            fal = min(1.0, max(0.0, (raide[k] - 0.18) / 0.30))
            brg = 0.0
            if masque[k]:
                brg = 1.0
            elif berge_pres[k]:
                brg = 0.85
            elif berge_loin[k]:
                brg = 0.35
            brg *= (1.0 - fal)
            c = cls[k]
            sous = 0.0
            gar = 0.0
            if c in (2, 3, 4):              # ripisylve, chêne vert, pubescent
                sous = 1.0
            elif c == 1:                    # rocher
                fal = max(fal, 0.75)
            else:                           # garrigue, pelouse, eau
                gar = 1.0
            reste = max(0.0, 1.0 - fal - brg)
            sous *= reste
            gar *= reste
            if sous + gar < 1e-6:
                gar = reste
            som = fal + gar + sous + brg + 1e-6
            couches[k*4]   = int(255 * fal / som)
            couches[k*4+1] = int(255 * gar / som)
            couches[k*4+2] = int(255 * sous / som)
            couches[k*4+3] = int(255 * brg / som)
    top("couleurs, ombrage et couches de matière")

    # ── arbres : on jette ceux qui tombent dans l'eau ou sur la berge.
    # C'est LE correctif du bug 2 : semis.py classait par accumulation
    # d'écoulement et ne voyait pas la rivière ; le masque BD TOPO, si.
    interdit = dilate(masque, n, pas, MARGE_BERGE)
    idx = {nom: k for k, nom in enumerate(noms)}
    gardes, jetes = bytearray(), 0
    for a in d["arbres"]:
        x, zz = a[0], a[1]
        i, j = int(x / pas), int(zz / pas)
        if 0 <= i < n and 0 <= j < n and interdit[j * n + i]:
            jetes += 1
            continue
        # la variante du semis est conservée : c'est elle qui évitera une forêt
        # de clones, en piochant dans plusieurs formes du même arbre
        gardes += struct.pack("<ffBfB", x, zz, idx.get(a[3], 0), a[4], int(a[5]) & 255)
    n_arb = len(gardes) // 14
    top(f"semis : {n_arb} arbres gardés, {jetes} jetés (eau + {MARGE_BERGE:.0f} m de berge)")

    # ── écriture
    p = lambda f: os.path.join(RACINE, "data", f)
    os.makedirs(os.path.join(RACINE, "data"), exist_ok=True)
    open(p("terrain.bin"), "wb").write(struct.pack(f"<{n*n}f", *Zc))
    open(p("couleurs.bin"), "wb").write(bytes(coul))
    open(p("lumiere.bin"), "wb").write(bytes(lumi))
    open(p("couches.bin"), "wb").write(bytes(couches))
    open(p("eau.bin"), "wb").write(struct.pack(f"<{n*n}f", *eau))
    open(p("arbres.bin"), "wb").write(bytes(gardes))
    zmin, zmax = min(Zc), max(Zc)
    json.dump({
        "n": n, "pas_m": pas, "emprise_m": emprise,
        "z_min": zmin, "z_max": zmax,
        "lat_top": d["lat_top"], "lon_left": d["lon_left"], "source": d["source"],
        "noms": noms, "n_arbres": n_arb, "arbres_jetes": jetes,
        "origine": os.path.basename(SRC), "facteur": FACT,
        "reglages": {"lissage_m": LISSAGE, "aplatissement": APLATIR,
                     "creusement": CREUSER, "eau_offset_m": EAU_OFF},
        "echelle_lum": ECHELLE_LUM,
        "couches": ["falaise", "garrigue", "sousbois", "berge"],
    }, open(p("monde.json"), "w"), indent=1, ensure_ascii=False)

    print(f"\nterrain {zmin:.1f} → {zmax:.1f} m ({zmax-zmin:.0f} m de dénivelé)")
    print(f"écrit dans data/ en {time.time()-t0:.1f} s")


if __name__ == "__main__":
    main()
