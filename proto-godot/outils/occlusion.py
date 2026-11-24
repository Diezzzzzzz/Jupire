#!/usr/bin/env python3
"""
Combien d'orientations de caméra le relief de Balazuc bouche-t-il vraiment ?

C'est LA question qui décide entre « yaw verrouillé » (un seul rendu par objet)
et « paliers de 45° ». On la tranche en comptant, pas à l'œil : pour un
échantillon de points du terrain, on tire un rayon vers la caméra orthographique
sous chacun des 8 paliers et on regarde si le sol passe devant.

    python3 outils/occlusion.py

Lit data/terrain.bin + data/eau.bin (donc le terrain DÉJÀ transformé, avec
l'aplatissement 0,85 et le creusement ×1,1 — c'est bien celui qu'on regarde).
"""

import json, math, os, struct, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(RACINE, "data")

TILTS = [20.0, 26.565, 30.0, 36.0, 45.0]   # 26,565° = atan(0.5), le 2:1 d'AoE2
ANGLES = 8
PORTEE_RAYON = 900.0      # m suivis le long du rayon
PAS_RAYON = 5.0
OEIL = 1.6                # hauteur des yeux


def main():
    meta = json.load(open(os.path.join(D, "monde.json")))
    n, pas = meta["n"], meta["pas_m"]
    emprise = n * pas
    z = struct.unpack(f"<{n*n}f", open(os.path.join(D, "terrain.bin"), "rb").read())
    eau = struct.unpack(f"<{n*n}f", open(os.path.join(D, "eau.bin"), "rb").read())
    plafond = max(z) + 0.6

    def alt(x, zz):
        fx = min(max(x / pas, 0.0), n - 1.001)
        fz = min(max(zz / pas, 0.0), n - 1.001)
        i, j = int(fx), int(fz)
        u, v = fx - i, fz - j
        k = j * n + i
        return ((z[k] * (1 - u) + z[k + 1] * u) * (1 - v)
                + (z[k + n] * (1 - u) + z[k + n + 1] * u) * v)

    # échantillon : une grille de points hors eau, plus un sous-ensemble
    # « berge » (à moins de 40 m d'une eau) — c'est le fond de gorge.
    saut = max(1, int(20.0 / pas))
    rb = max(1, int(40.0 / pas))
    points, berges = [], []
    for j in range(saut, n - saut, saut):
        for i in range(saut, n - saut, saut):
            k = j * n + i
            if eau[k] == eau[k]:          # NaN = hors eau
                continue
            p = (i * pas, j * pas, z[k])
            points.append(p)
            proche = False
            for dj in (-rb, 0, rb):
                for di in (-rb, 0, rb):
                    kk = min(max(j + dj, 0), n - 1) * n + min(max(i + di, 0), n - 1)
                    if eau[kk] == eau[kk]:
                        proche = True
            if proche:
                berges.append(p)

    print(f"{len(points)} points de terrain, dont {len(berges)} de berge "
          f"(grille de {saut*pas:.0f} m)\n")
    print(f"{'incl.':>8} {'pentes':>7} │ {'terrain entier':^30} │ {'fond de gorge':^30}")
    print(f"{'':>8} {'perçues':>7} │ {'moy /8':>7} {'≥1 bouché':>11} {'tout bouché':>11} │"
          f" {'moy /8':>7} {'≥1 bouché':>11} {'tout bouché':>11}")
    print("─" * 96)

    for tdeg in TILTS:
        t = math.radians(tdeg)
        dirs = []
        for a in range(ANGLES):
            az = 2 * math.pi * a / ANGLES
            dirs.append((math.sin(az) * math.cos(t), math.sin(t), math.cos(az) * math.cos(t)))

        res = {}
        for nom, ens in (("tout", points), ("berge", berges)):
            somme = tous = au_moins = 0
            for (px, pz, py) in ens:
                by = py + OEIL
                b = 0
                for (dx, dy, dz) in dirs:
                    s = PAS_RAYON
                    bouche = False
                    while s < PORTEE_RAYON:
                        x, y, zz = px + dx * s, by + dy * s, pz + dz * s
                        # Sorti par le haut : plus rien ne peut passer devant,
                        # le point le plus haut du monde est déjà sous le rayon.
                        if y > plafond:
                            break
                        if x < 0 or zz < 0 or x >= emprise or zz >= emprise:
                            break
                        if alt(x, zz) > y + 0.6:
                            bouche = True
                            break
                        s += PAS_RAYON
                    if bouche:
                        b += 1
                somme += b
                if b > 0:
                    au_moins += 1
                if b == ANGLES:
                    tous += 1
            m = len(ens)
            res[nom] = (somme / m, 100.0 * au_moins / m, 100.0 * tous / m)

        exa = math.tan(math.radians(90 - tdeg))
        a, b = res["tout"], res["berge"]
        print(f"{tdeg:8.3f} {exa:6.2f}× │ {a[0]:7.2f} {a[1]:10.1f} % {a[2]:10.1f} % │"
              f" {b[0]:7.2f} {b[1]:10.1f} % {b[2]:10.1f} %")

    print("\nLecture : « ≥1 bouché » = points où AU MOINS une des 8 orientations")
    print("est masquée — donc où un yaw verrouillé a une chance de tomber mal.")
    print("« tout bouché » = points qu'AUCUNE des 8 orientations ne dégage :")
    print("là, même la rotation ne sauve pas, il faut fondre le relief occultant.")


if __name__ == "__main__":
    main()
