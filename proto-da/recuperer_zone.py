#!/usr/bin/env python3
"""Récupère une zone réelle chez l'IGN et l'écrit pour proto-brouillard.html.

    python3 proto-da/recuperer_zone.py vinezac 44.5400 4.3092 3400 1600 --depart 44.5391 4.3252
    python3 proto-da/recuperer_zone.py <nom> <lat> <lon> <largeur_m> [hauteur_m] [--depart lat lon] [--bati]

Sorties : proto-da/donnees-<nom>.js (relief, eau, lits à sec, couvert végétal, arbres)
          proto-da/ortho-<nom>.js (orthophoto IGN à 1 m, pour la vue satellite du proto).
Les téléchargements bruts sont gardés dans proto-da/brut/ : relancer ne retélécharge pas.

Par défaut : terrain seul. Les bâtiments et les routes de la BD TOPO servent seulement à ne
pas planter d'arbre à leur emplacement ; --bati les met dans le jeu.

Sources (Géoplateforme IGN, sans clé) :
  - MNT LiDAR HD : altitude du sol, 1 m                       (WMS raster)
  - MNH LiDAR HD : hauteur au-dessus du sol (arbres, toits)   (WMS raster)
  - BD TOPO : bâtiments, surfaces d'eau, ruisseaux, routes,
              zones de végétation (bois, forêt, haie…)        (WFS vecteur)

Eau : seuls les cours d'eau PERMANENTS sont en eau. Les ruisseaux intermittents de la BD TOPO
(à sec presque toute l'année) deviennent des lits de galets à sec.

Végétation : tout vient de la hauteur mesurée par le LiDAR (MNH).
  plus de 4 m    -> un arbre par couronne ; le proto choisit l'essence (bois de la BD TOPO, vergers = oliviers,
                    exposition du versant, bord de l'eau)
  1,5 à 4 m      -> buissons
  0,3 à 1,5 m    -> broussailles (dessinées comme une matière de sol, grille « couvert »)
Seul ajout qui ne vient pas d'une mesure : une ripisylve le long de l'eau (arbres et buissons à moins de 6 m).

Python pur : ni numpy ni Pillow.
"""
import base64, json, math, os, struct, sys, time, urllib.request

args = sys.argv[1:]
AVEC_BATI = "--bati" in args
if AVEC_BATI:
    args.remove("--bati")
DEPART = None
if "--depart" in args:
    k = args.index("--depart")
    DEPART = (float(args[k + 1]), float(args[k + 2]))
    del args[k:k + 3]
NOM = args[0]
LAT_C, LON_C = float(args[1]), float(args[2])
LARG = int(args[3]) if len(args) > 3 else 600
HAUT = int(args[4]) if len(args) > 4 else LARG
NX, NY = LARG + 1, HAUT + 1
NN = NX * NY
ICI = os.path.dirname(os.path.abspath(__file__))
BRUT = os.path.join(ICI, "brut")
os.makedirs(BRUT, exist_ok=True)

M_LAT = 111_320.0
M_LON = 111_320.0 * math.cos(math.radians(LAT_C))
LAT_N, LAT_S = LAT_C + NY / 2 / M_LAT, LAT_C - NY / 2 / M_LAT
LON_O, LON_E = LON_C - NX / 2 / M_LON, LON_C + NX / 2 / M_LON
T0 = time.time()


def etape(texte):
    print(f"[{time.time() - T0:5.0f} s] {texte}", flush=True)


def telecharger(fichier, url):
    chemin = os.path.join(BRUT, f"{NOM}_{LARG}x{HAUT}_{LAT_C}_{LON_C}_{fichier}")      # le cache dépend de l'emprise
    if os.path.exists(chemin) and os.path.getsize(chemin) > 100:
        return open(chemin, "rb").read()
    for essai in range(6):          # le service renvoie des 400/502 par intermittence
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
            with urllib.request.urlopen(req, timeout=300) as r:
                brut = r.read()
            if brut[:5] == b"<?xml" or b"ServiceException" in brut[:800]:
                raise RuntimeError(brut[:200])
            open(chemin, "wb").write(brut)
            return brut
        except Exception as e:
            if essai == 5:
                sys.exit(f"échec {fichier} : {e}")
            time.sleep(2 * (essai + 1))


def raster(nom, couche):
    """Grille NX x NY à 1 m. Le WMS plafonne vers 2048 px de côté : on découpe et on recolle."""
    z = [0.0] * NN
    tx, ty = math.ceil(NX / 2000), math.ceil(NY / 2000)
    for b in range(ty):
        for a in range(tx):
            x0, x1 = a * NX // tx, (a + 1) * NX // tx
            y0, y1 = b * NY // ty, (b + 1) * NY // ty
            w, h = x1 - x0, y1 - y0
            lo0, lo1 = LON_O + (LON_E - LON_O) * x0 / NX, LON_O + (LON_E - LON_O) * x1 / NX
            la1, la0 = LAT_N - (LAT_N - LAT_S) * y0 / NY, LAT_N - (LAT_N - LAT_S) * y1 / NY
            u = ("https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
                 f"&LAYERS={couche}&STYLES=&CRS=EPSG:4326&BBOX={la0},{lo0},{la1},{lo1}"
                 f"&WIDTH={w}&HEIGHT={h}&FORMAT=image/x-bil;bits=32")
            v = struct.unpack(f"<{w * h}f", telecharger(f"{nom}_{a}_{b}.bil", u)[:w * h * 4])
            for j in range(h):
                z[(y0 + j) * NX + x0:(y0 + j) * NX + x1] = v[j * w:(j + 1) * w]
    return z


def vecteur(couche):
    """Tous les objets d'une couche BD TOPO dans l'emprise (le WFS rend 5000 objets par page)."""
    objets, debut = [], 0
    while True:
        u = ("https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
             f"&TYPENAMES=BDTOPO_V3:{couche}&BBOX={LAT_S},{LON_O},{LAT_N},{LON_E},urn:ogc:def:crs:EPSG::4326"
             f"&OUTPUTFORMAT=application/json&COUNT=5000&STARTINDEX={debut}")
        page = json.loads(telecharger(f"{couche}_{debut}.json", u))["features"]
        objets += page
        if len(page) < 5000:
            return objets
        debut += 5000


def xy(p):                          # (lon, lat) -> mètres depuis le coin nord-ouest
    return (p[0] - LON_O) * M_LON - 0.5, (LAT_N - p[1]) * M_LAT - 0.5


def remplir(masque, anneaux):
    """Remplissage pair-impair d'un polygone (avec trous) dans la grille à 1 m."""
    pts = [[xy(p) for p in a] for a in anneaux]
    ys = [p[1] for a in pts for p in a]
    aretes = [(x0, y0, x1, y1) for a in pts for (x0, y0), (x1, y1) in zip(a, a[1:]) if y0 != y1]
    for j in range(max(0, math.floor(min(ys))), min(NY - 1, math.ceil(max(ys))) + 1):
        xs = sorted(x0 + (j - y0) * (x1 - x0) / (y1 - y0) for x0, y0, x1, y1 in aretes if (y0 <= j) != (y1 <= j))
        for a, b in zip(xs[::2], xs[1::2]):
            for i in range(max(0, math.ceil(a)), min(NX - 1, math.floor(b)) + 1):
                masque[j * NX + i] = 1


def tracer(masque, ligne, largeur):
    pts = [xy(p) for p in ligne]
    r = largeur / 2
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        l2 = dx * dx + dy * dy or 1e-9
        for j in range(max(0, int(min(y0, y1) - r)), min(NY - 1, int(max(y0, y1) + r) + 1) + 1):
            for i in range(max(0, int(min(x0, x1) - r)), min(NX - 1, int(max(x0, x1) + r) + 1) + 1):
                t = max(0, min(1, ((i - x0) * dx + (j - y0) * dy) / l2))
                if math.hypot(i - x0 - t * dx, j - y0 - t * dy) <= r:
                    masque[j * NX + i] = 1


def polygones(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else []


def lignes(geom):
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    return geom["coordinates"] if geom["type"] == "MultiLineString" else []


etape(f"{NOM} · {LARG} x {HAUT} m autour de {LAT_C}, {LON_C}")
mnt = raster("mnt", "IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.WGS84G")
mnh = raster("mnh", "IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.WGS84G")
etape("relief et hauteurs téléchargés")
ok = [v for v in mnt if -500 < v < 5000]
if len(ok) < NN * 0.9:
    sys.exit(f"relief incomplet : {len(ok)} altitudes valides sur {NN} (zone hors couverture LiDAR HD ?)")
moy = sum(ok) / len(ok)
mnt = [v if -500 < v < 5000 else moy for v in mnt]
mnh = [v if 0 < v < 60 else 0.0 for v in mnh]
zmin, zmax = min(mnt), max(mnt)

bati, eau, lit, chemin, bois, verger, peuplement = (bytearray(NN) for _ in range(7))
batiments = vecteur("batiment")
for f in batiments:
    for poly in polygones(f["geometry"]):
        remplir(bati, poly)
for f in vecteur("surface_hydrographique"):
    if f["properties"].get("persistance") in (None, "Permanent"):
        for poly in polygones(f["geometry"]):
            remplir(eau, poly)
ruisseaux = vecteur("troncon_hydrographique")
permanents = intermittents = 0
LARGEURS = {"Entre 0 et 5 m": 2.5, "Entre 5 et 15 m": 6.0, "Entre 15 et 50 m": 16.0, "Plus de 50 m": 40.0}
for f in ruisseaux:
    p = f["properties"]
    if p.get("position_par_rapport_au_sol") not in (None, "0"):
        continue
    if p.get("persistance") == "Permanent":
        permanents += 1
        for l in lignes(f["geometry"]):
            tracer(eau, l, LARGEURS.get(p.get("classe_de_largeur"), 2.5))
    else:
        intermittents += 1
        for l in lignes(f["geometry"]):
            tracer(lit, l, 2.0)
routes = vecteur("troncon_de_route")
for f in routes:
    larg = f["properties"].get("largeur_de_chaussee") or 2.5
    for l in lignes(f["geometry"]):
        tracer(chemin, l, max(2.0, min(4.0, larg)))
zones = vecteur("zone_de_vegetation")
for f in zones:
    nature = f["properties"].get("nature") or ""
    if nature.split()[0] in ("Bois", "Forêt", "Haie", "Verger"):
        for poly in polygones(f["geometry"]):
            remplir(verger if nature == "Verger" else bois, poly)      # les vergers du Sud-Ardèche : des oliviers
    # Type de peuplement de la BD TOPO, pour que le proto choisisse les essences : 1 feuillus, 2 conifères, 3 mixte, 4 verger, 5 lande.
    code = 2 if "conifères" in nature else 3 if "mixte" in nature else 4 if nature == "Verger" else 5 if nature.startswith("Lande") else 1 if nature.split()[0] in ("Bois", "Forêt", "Haie") else 0
    if code:
        m = bytearray(NN)
        for poly in polygones(f["geometry"]):
            remplir(m, poly)
        for k in range(NN):
            if m[k]:
                peuplement[k] = code
for k in range(NN):
    if bati[k]:
        eau[k] = 0; chemin[k] = 0
    if eau[k]:
        chemin[k] = 0; lit[k] = 0
etape(f"{len(batiments)} bâtiments, {len(routes)} tronçons de route, {permanents} tronçons d'eau permanents, "
      f"{intermittents} intermittents, {len(zones)} zones de végétation")

toit = None
if AVEC_BATI:
    # Hauteur des bâtiments : le MNH borné à 2,5–25 m, adouci trois fois à l'intérieur de l'emprise.
    toit = [max(2.5, min(25.0, mnh[k])) if bati[k] else 0.0 for k in range(NN)]
    cases = [k for k in range(NN) if bati[k] and NX <= k < NN - NX]
    for _ in range(3):
        suivant = toit[:]
        for k in cases:
            s = n = 0
            for v in (k - NX - 1, k - NX, k - NX + 1, k - 1, k, k + 1, k + NX - 1, k + NX, k + NX + 1):
                if bati[v]:
                    s += toit[v]; n += 1
            suivant[k] = s / n
        toit = suivant


# ---------------------------------------------------------------- végétation
def h01(i, j, sel=0):               # tirage déterministe 0..1 par case
    n = (i * 73856093) ^ (j * 19349663) ^ (sel * 83492791)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


lisse = [0.0] * NN
for j in range(1, NY - 1):
    r = j * NX
    for k in range(r + 1, r + NX - 1):
        lisse[k] = (mnh[k] * 4 + mnh[k - 1] + mnh[k + 1] + mnh[k - NX] + mnh[k + NX]) / 8
interdit = bytearray(NN)
for k in range(NN):
    if eau[k] or chemin[k]:
        interdit[k] = 1
    elif bati[k]:                   # le bâti interdit aussi les 2 m autour
        i, j = k % NX, k // NX
        for b in range(max(0, j - 2), min(NY, j + 3)):
            for a in range(max(0, i - 2), min(NX, i + 3)):
                interdit[b * NX + a] = 1
# Distance à l'eau, jusqu'à 6 m (pour la ripisylve).
pres_eau = bytearray(NN)
front = [k for k in range(NN) if eau[k]]
for d in range(1, 7):
    suivant = []
    for k in front:
        for v in (k - 1, k + 1, k - NX, k + NX):
            if 0 <= v < NN and not eau[v] and not pres_eau[v]:
                pres_eau[v] = d; suivant.append(v)
    front = suivant
etape("grilles de végétation prêtes")

pris = bytearray(NN)
arbres = []
compte = {"arbres": 0, "buissons": 0, "ripisylve": 0}


def planter(i, j, h, force=None):
    k = j * NX + i
    tirage = int(h01(i, j, 1) * 100)
    if force is not None:
        esp = force
    elif h < 4:
        esp = 0
    else:
        esp = 4 if (bois[k] and tirage < 75) or (not bois[k] and tirage < 15) else 3
    ech = max(0.6, min(1.6, h / 2.2)) if esp == 0 else max(0.5, min(1.35, h / 8.0))
    arbres.extend([int((i + (h01(i, j, 2) - 0.5) * 0.8) * 10), int((j + (h01(i, j, 3) - 0.5) * 0.8) * 10), esp, int(ech * 100), tirage])
    r = max(1.6, min(3.2, 0.2 * h + 0.6)) if h >= 4 else 1.3       # chacun réserve la place de sa couronne
    ri = int(r)
    for b in range(-ri, ri + 1):
        for a in range(-ri, ri + 1):
            if a * a + b * b <= r * r and 0 <= i + a < NX and 0 <= j + b < NY:
                pris[(j + b) * NX + i + a] = 1
    compte["ripisylve" if force is not None else "arbres" if h >= 4 else "buissons"] += 1


# 1. Les sommets de la canopée, les plus hauts d'abord.
sommets = []
voisins = (-NX - 1, -NX, -NX + 1, -1, 1, NX - 1, NX, NX + 1)
for j in range(4, NY - 4):
    r = j * NX
    for k in range(r + 4, r + NX - 4):
        h = lisse[k]
        if h >= 1.5 and not interdit[k]:
            for v in voisins:
                if lisse[k + v] > h:
                    break
            else:
                sommets.append((h, k))
sommets.sort(reverse=True)
for h, k in sommets:
    if not pris[k]:
        planter(k % NX, k // NX, h)
etape(f"sommets de canopée plantés ({len(sommets)} candidats)")
# 2. Les nappes de canopée sans sommet net (forêt fermée, fourrés) : une trame de 2 m comble les trous.
for j in range(4, NY - 4, 2):
    for i in range(4 + (j // 2) % 2, NX - 4, 2):
        k = j * NX + i
        if lisse[k] >= 1.5 and not interdit[k] and not pris[k]:
            planter(i, j, lisse[k])
# 3. Ripisylve : le long de l'eau, arbres tous les ~3 m et buissons entre eux, là où rien n'est déjà planté.
for k in range(NN):
    if not pres_eau[k] or interdit[k] or pris[k]:
        continue
    i, j = k % NX, k // NX
    if not (4 <= i < NX - 4 and 4 <= j < NY - 4):
        continue
    t = h01(i, j, 4)
    if pres_eau[k] >= 2 and t < 0.10:
        planter(i, j, 6 + h01(i, j, 5) * 6, force=9)
    elif t > 0.80:
        planter(i, j, 1.6 + h01(i, j, 6) * 1.6, force=0)

# Couvert : hauteur de végétation par case (dm), hors bâti et eau, pour dessiner broussailles et sous-bois au sol.
# Autour des bâtiments, le MNH garde un liseré de hauteur (murs, débords de toit, emprises BD TOPO un peu
# décalées) : sans l'effacer, chaque maison retirée laissait un anneau brun de « sous-bois » et une ville
# entière dessinait un réseau de lignes. On remet donc le couvert à zéro jusqu'à 3 m du bâti.
pres_bati = bytearray(NN)
for k in range(NN):
    if bati[k]:
        i, j = k % NX, k // NX
        for b in range(max(0, j - 3), min(NY, j + 4)):
            pres_bati[b * NX + max(0, i - 3):b * NX + min(NX, i + 4)] = b"\x01" * (min(NX, i + 4) - max(0, i - 3))
couvert = bytearray(NN)
for k in range(NN):
    if not pres_bati[k] and not eau[k]:
        couvert[k] = min(255, int(lisse[k] * 10))
        if pres_eau[k] and couvert[k] < 8:
            couvert[k] = 8          # berges toujours enherbées haut
etape("végétation plantée")

# Départ : la case hors de l'eau la plus proche du point demandé (ou du centre).
if DEPART:
    dx, dy = xy((DEPART[1], DEPART[0]))
else:
    dx, dy = NX / 2, NY / 2
dx, dy = int(max(12, min(NX - 13, dx))), int(max(12, min(NY - 13, dy)))
depart = min(((abs(a) + abs(b), dx + a, dy + b) for b in range(-10, 11) for a in range(-10, 11)
              if not eau[(dy + b) * NX + dx + a] and (not AVEC_BATI or not bati[(dy + b) * NX + dx + a])), default=(0, dx, dy))[1:]


def bits(m):
    out = bytearray((NN + 7) // 8)
    for k in range(NN):
        if m[k]:
            out[k >> 3] |= 1 << (k & 7)
    return base64.b64encode(bytes(out)).decode()


sortie = {
    "nom": NOM, "nx": NX, "ny": NY, "zmin": round(zmin, 2), "zmax": round(zmax, 2),
    "rotation_defaut": 0, "depart": list(depart),
    "lat_nord": round(LAT_N, 5), "lon_ouest": round(LON_O, 5),
    "source": "IGN LiDAR HD (MNT et MNH à 1 m) et BD TOPO, Géoplateforme",
    "alt_cm_u16": base64.b64encode(struct.pack(f"<{NN}H", *[int(round((v - zmin) * 100)) for v in mnt])).decode(),
    "eau_bits": bits(eau), "lit_bits": bits(lit), "peuplement_u8": base64.b64encode(bytes(peuplement)).decode(), "eau_stricte": True, "hameau": False,
    "couvert_dm_u8": base64.b64encode(bytes(couvert)).decode(),
}
if AVEC_BATI:
    sortie["chemin_bits"] = bits(chemin)
    sortie["bati_dm_u8"] = base64.b64encode(bytes(int(v * 10) for v in toit)).decode()
chemin_js = os.path.join(ICI, f"donnees-{NOM}.js")
with open(chemin_js, "w") as f:
    f.write("window.DONNEES = " + json.dumps(sortie) + ";\n")
    f.write("window.ARBRES = " + json.dumps(arbres, separators=(",", ":")) + ";\n")
etape(f"écrit {chemin_js} ({os.path.getsize(chemin_js) / 1e6:.0f} Mo)")

# Orthophoto IGN à 1 m, pour la vue satellite du proto (touche O). Les JPEG restent en morceaux :
# on ne sait pas les recoller sans bibliothèque d'image, le navigateur le fait au chargement.
morceaux = []
tx, ty = math.ceil(NX / 2000), math.ceil(NY / 2000)
for b in range(ty):
    for a in range(tx):
        x0, x1 = a * NX // tx, (a + 1) * NX // tx
        y0, y1 = b * NY // ty, (b + 1) * NY // ty
        lo0, lo1 = LON_O + (LON_E - LON_O) * x0 / NX, LON_O + (LON_E - LON_O) * x1 / NX
        la1, la0 = LAT_N - (LAT_N - LAT_S) * y0 / NY, LAT_N - (LAT_N - LAT_S) * y1 / NY
        u = ("https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
             f"&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS&STYLES=&CRS=EPSG:4326&BBOX={la0},{lo0},{la1},{lo1}"
             f"&WIDTH={x1 - x0}&HEIGHT={y1 - y0}&FORMAT=image/jpeg")
        jpeg = telecharger(f"ortho_{a}_{b}.jpg", u)
        if jpeg[:2] != b"\xff\xd8":
            sys.exit(f"orthophoto : réponse inattendue {jpeg[:80]!r}")
        morceaux.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "jpeg": base64.b64encode(jpeg).decode()})
chemin_ortho = os.path.join(ICI, f"ortho-{NOM}.js")
with open(chemin_ortho, "w") as f:
    f.write("window.ORTHO_TUILES = " + json.dumps(morceaux) + ";\n")
etape(f"écrit {chemin_ortho} ({os.path.getsize(chemin_ortho) / 1e6:.1f} Mo, {len(morceaux)} morceaux)")
print(f"altitude {zmin:.1f} → {zmax:.1f} m · eau {sum(eau)} m² · lits à sec {sum(lit)} m² · "
      f"végétation : {compte['arbres']} arbres, {compte['buissons']} buissons, {compte['ripisylve']} en ripisylve · "
      f"couvert LiDAR : {sum(1 for v in couvert if v >= 40) * 100 // NN} % arbres, "
      f"{sum(1 for v in couvert if 15 <= v < 40) * 100 // NN} % buissons, {sum(1 for v in couvert if 3 <= v < 15) * 100 // NN} % broussailles · départ {depart}")
