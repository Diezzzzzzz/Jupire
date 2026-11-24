#!/usr/bin/env python3
"""Récupère les calques d'appui (orthophoto, hydrographie) POUR UN MONDE DONNÉ.

Chaque monde a sa propre emprise : un calque récupéré pour une autre emprise plaque
la rivière n'importe où. Les fichiers sont donc nommés d'après le monde :
    world.json  →  world.ortho.jpg  ·  world.hydro.png

Usage :  calques.py [world.json ...]      (défaut : tous les data/world*.json)
Zéro dépendance : stdlib seulement.
"""
import glob, json, math, os, sys, time, urllib.request

WMS = "https://data.geopf.fr/wms-r/wms"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
CALQUES = [
    ("ortho.jpg", "ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg", ""),
    ("hydro.png", "IGNF_HYDROGRAPHY.HYDROGRAPHY", "image/png", "&TRANSPARENT=TRUE"),
]


def pour(chemin):
    nom = os.path.basename(chemin)[:-5]           # « world_1200 »
    with open(chemin) as f:
        m = json.load(f)
    if m.get("lat_top") is None:
        print(f"{nom:16} emprise absente du fichier — relancer semis.py")
        return
    w, h, step = m["w"], m["h"], m["step_m"]
    lat_top, lon_left = m["lat_top"], m["lon_left"]
    larg, haut = (w-1)*step, (h-1)*step
    lat_c = lat_top - haut/2/111_320
    dlon = larg / (111_320 * math.cos(math.radians(lat_c)))
    lon_right = lon_left + dlon
    lat_bot = lat_top - haut/111_320
    bbox = f"{lat_bot},{lon_left},{lat_top},{lon_right}"   # 1.3.0 : lat,lon

    iw = min(1536, w); ih = max(64, round(iw * haut / larg))
    print(f"{nom:16} {larg:.0f}×{haut:.0f} m → {iw}×{ih}")
    for suffixe, couche, fmt, extra in CALQUES:
        cible = os.path.join(DATA, f"{nom}.{suffixe}")
        u = (f"{WMS}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={couche}&STYLES="
             f"&CRS=EPSG:4326&BBOX={bbox}&WIDTH={iw}&HEIGHT={ih}&FORMAT={fmt}{extra}")
        # le WMS renvoie par intermittence des 400/502 sans raison : on réessaie
        for essai in range(6):
            try:
                with urllib.request.urlopen(u, timeout=240) as r:
                    img = r.read()
                if img[:2] == b"\xff\xd8" or img[:4] == b"\x89PNG":
                    open(cible, "wb").write(img)
                    print(f"   {suffixe:10} {len(img)/1000:5.0f} ko")
                    break
                print(f"   {suffixe:10} refusé par le WMS"); break
            except Exception as e:
                if essai == 5:
                    print(f"   {suffixe:10} échec après 6 essais : {e}")
                else:
                    time.sleep(2 * (essai + 1))


if __name__ == "__main__":
    cibles = sys.argv[1:] or sorted(glob.glob(os.path.join(DATA, "world*.json")))
    if not cibles:
        sys.exit("aucun monde trouvé dans data/")
    for c in cibles:
        pour(c)
