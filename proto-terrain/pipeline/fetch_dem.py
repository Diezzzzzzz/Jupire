#!/usr/bin/env python3
"""Récupère MNT + orthophoto + hydrographie via le WMS de la Géoplateforme.

Les couches ELEVATIONGRIDCOVERAGE se servent en `image/x-bil;bits=32` : une grille
d'altitudes entière en UNE requête. Les trois calques viennent du même service sur la
même bbox — donc alignés au pixel près, sans recalage.

Usage :  fetch_dem.py [largeur_m] [hauteur_m] [resolution_m] [source] [lat] [lon]
    défaut : 2400 2400 1.2 lidar (centré Balazuc)
    source : lidar (MNT LiDAR HD) | rge (RGE ALTI)

Zéro dépendance : stdlib seulement.
"""
import json, math, os, struct, sys, time, urllib.request

def arg(i, d, f=float):
    return f(sys.argv[i]) if len(sys.argv) > i else d

LARG_M = arg(1, 2400)
HAUT_M = arg(2, LARG_M)
RES_M  = arg(3, 1.2)
SRC    = arg(4, "lidar", str).lower()
LAT_C  = arg(5, 44.5089)          # Balazuc
LON_C  = arg(6, 4.3742)

COUCHES = {
    "lidar": "IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.WGS84G",
    "rge":   "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES",
}
WMS = "https://data.geopf.fr/wms-r/wms"
MAX = 2048                        # au-delà, le WMS devient très lent puis refuse
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "dem.json")


def main():
    if SRC not in COUCHES:
        sys.exit(f"source inconnue : {SRC} (lidar | rge)")

    # pas isotrope imposé par le moteur ; plus de plafond à 2048 : on mosaïque
    step = RES_M
    W, H = max(64, round(LARG_M / step)), max(64, round(HAUT_M / step))
    nx, ny = math.ceil(W / MAX), math.ceil(H / MAX)

    dlat = HAUT_M / 2 / 111_320
    dlon = LARG_M / 2 / (111_320 * math.cos(math.radians(LAT_C)))
    bbox = f"{LAT_C-dlat},{LON_C-dlon},{LAT_C+dlat},{LON_C+dlon}"   # 1.3.0 : lat,lon

    print(f"{SRC} · {LARG_M:.0f} × {HAUT_M:.0f} m · {W}×{H} · pas {step:.2f} m"
          + (f" · mosaïque {nx}×{ny}" if nx*ny > 1 else ""), flush=True)

    # Le WMS plafonne vers 2048 px par côté : au-delà on découpe et on recolle.
    # C'est ce qui permet la haute résolution sur une grande emprise.
    z = [0.0] * (W * H)
    for ty in range(ny):
        for tx in range(nx):
            x0, x1 = tx * W // nx, (tx + 1) * W // nx
            y0, y1 = ty * H // ny, (ty + 1) * H // ny
            tw, th = x1 - x0, y1 - y0
            # bbox de la tuile, en fraction de l'emprise totale
            la_h = (LAT_C + dlat) - 2*dlat * (y0 / H)
            la_b = (LAT_C + dlat) - 2*dlat * (y1 / H)
            lo_g = (LON_C - dlon) + 2*dlon * (x0 / W)
            lo_d = (LON_C - dlon) + 2*dlon * (x1 / W)
            u = (f"{WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                 f"&LAYERS={COUCHES[SRC]}&STYLES=&CRS=EPSG:4326"
                 f"&BBOX={la_b},{lo_g},{la_h},{lo_d}"
                 f"&WIDTH={tw}&HEIGHT={th}&FORMAT=image/x-bil;bits=32")
            # le WMS renvoie par intermittence des 400/502 sans raison : on réessaie
            brut = None
            for essai in range(6):
                try:
                    with urllib.request.urlopen(u, timeout=300) as r:
                        brut = r.read()
                    break
                except Exception as e:
                    if essai == 5:
                        sys.exit(f"WMS injoignable après 6 essais : {e}")
                    print(f"   ({e} — nouvel essai dans {2*(essai+1)} s)", flush=True)
                    time.sleep(2 * (essai + 1))
            if b"ServiceException" in brut[:800] or brut[:5] == b"<?xml":
                sys.exit(f"WMS a répondu une erreur : {brut[:300]!r}")
            vals = struct.unpack(f"<{tw*th}f", brut[:tw*th*4])
            for j in range(th):
                z[(y0+j)*W + x0 : (y0+j)*W + x1] = vals[j*tw:(j+1)*tw]
            if nx*ny > 1:
                print(f"   tuile {ty*nx+tx+1}/{nx*ny}", flush=True)
    ok = [v for v in z if -500 < v < 5000]
    if not ok:
        sys.exit("aucune altitude valide (hors emprise ?)")
    moy = sum(ok) / len(ok)
    z = [v if -500 < v < 5000 else moy for v in z]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"w": W, "h": H, "step_m": round(step, 3), "source": SRC,
                   "lat_top": LAT_C + dlat, "lon_left": LON_C - dlon,
                   "z": [round(v, 2) for v in z]}, f)
    print(f"OK → {OUT} ({os.path.getsize(OUT)/1e6:.1f} Mo)")
    print(f"   altitude {min(z):.1f} → {max(z):.1f} m · dénivelé {max(z)-min(z):.1f} m")

    # calques d'appui, même service, même bbox → alignement garanti
    dossier = os.path.dirname(OUT)
    ratio = HAUT_M / LARG_M
    iw = min(1536, W * 2); ih = max(64, round(iw * ratio))
    for nom, couche, fmt, extra in [
        ("ortho.jpg", "ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg", ""),
        # le vrai tracé des cours d'eau : deviner la rivière depuis le relief ne marche
        # pas (« plat et bas » attrape aussi terrasses, gravières et champs alluviaux)
        ("hydro.png", "IGNF_HYDROGRAPHY.HYDROGRAPHY", "image/png", "&TRANSPARENT=TRUE"),
    ]:
        u = (f"{WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={couche}&STYLES="
             f"&CRS=EPSG:4326&BBOX={bbox}&WIDTH={iw}&HEIGHT={ih}&FORMAT={fmt}{extra}")
        try:
            with urllib.request.urlopen(u, timeout=240) as r:
                img = r.read()
            if img[:2] == b"\xff\xd8" or img[:4] == b"\x89PNG":
                open(os.path.join(dossier, nom), "wb").write(img)
                print(f"   {nom:11} {iw}×{ih}  {len(img)/1000:5.0f} ko")
            else:
                print(f"   {nom:11} refusé par le WMS")
        except Exception as e:
            print(f"   {nom:11} échec : {e}")


if __name__ == "__main__":
    main()
