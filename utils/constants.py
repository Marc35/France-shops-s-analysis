"""
Project constants: geographic reference tables, shop categories and
brand-harmonisation rules.

Everything here is a hand-written reference table (not an external
dataset): departments -> regions, groupings of OpenStreetMap shop types,
brand-matching patterns.
"""

# ---------------------------------------------------------------------------
# Source and licence
# ---------------------------------------------------------------------------
SOURCE_TITLE = "BAse Nationale des Commerces Ouverte (BANCO)"
SOURCE_URL = "https://www.data.gouv.fr/datasets/base-nationale-des-commerces-ouverte"
SOURCE_PRODUCER = "Ça reste ouvert / OpenStreetMap contributors"
SOURCE_PORTAL = "data.gouv.fr"
SOURCE_LICENSE = "Open Database License (ODbL)"
# Stable "latest" links from data.gouv.fr: they always point to the most recent file
SOURCE_DOWNLOAD_URL = "https://www.data.gouv.fr/api/1/datasets/r/3d612ad7-f726-4fe5-a353-bdf76c5a44c2"  # CSV export (zip)

# Second dataset (same portal): INSEE legal populations, per municipality
POP_SOURCE_TITLE = "Populations de référence 2023"
POP_SOURCE_URL = "https://www.data.gouv.fr/datasets/populations-de-reference"
POP_SOURCE_PRODUCER = "INSEE"
POP_SOURCE_LICENSE = "Licence Ouverte 2.0"
POP_DOWNLOAD_URL = "https://www.data.gouv.fr/api/1/datasets/r/ae305c99-d5a1-4854-b3bb-80b5cbe1f8e4"      # INSEE CSV (zip)
POP_MEASURE = "PMUN"        # "population municipale": people whose usual residence is in the municipality

# Seed used for every random sample (reproducibility)
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Departments and regions (2016 regional map)
# Region names: official French names, except the few that have a usual English name.
# ---------------------------------------------------------------------------
REGIONS = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Brittany": ["22", "29", "35", "56"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corsica": ["2A", "2B"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Normandy": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
    "Guadeloupe": ["971"],
    "Martinique": ["972"],
    "French Guiana": ["973"],
    "Réunion": ["974"],
    "Mayotte": ["976"],
}

# Reverse lookup: department code -> region
DEPT_TO_REGION = {dep: region for region, deps in REGIONS.items() for dep in deps}

OVERSEAS_DEPTS = {"971", "972", "973", "974", "976"}
MAINLAND_REGIONS = [r for r, deps in REGIONS.items() if not set(deps) & OVERSEAS_DEPTS]

# Department names are kept in French (proper nouns)
DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône",
    "14": "Calvados", "15": "Cantal", "16": "Charente", "17": "Charente-Maritime",
    "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud", "2B": "Haute-Corse",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault",
    "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère",
    "39": "Jura", "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne",
    "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise",
    "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin",
    "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe",
    "73": "Savoie", "74": "Haute-Savoie", "75": "Paris", "76": "Seine-Maritime",
    "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme",
    "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse", "85": "Vendée",
    "86": "Vienne", "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion",
    "976": "Mayotte",
}

# Approximate bounding box of mainland France (used to validate coordinates)
METRO_BBOX = {"lon_min": -5.5, "lon_max": 10.0, "lat_min": 41.0, "lat_max": 51.5}

# ---------------------------------------------------------------------------
# Essential shops (part 1): label -> OSM types
# ---------------------------------------------------------------------------
ESSENTIAL_CATEGORIES = {
    "Bakery": ["bakery"],
    "Pharmacy": ["pharmacy"],
    "Supermarket": ["supermarket"],
    "Convenience store": ["convenience"],
    "Butcher": ["butcher"],
    "Greengrocer": ["greengrocer"],
    "Post office": ["post_office"],
    "Fuel station": ["fuel"],
}

# Plural forms, for headings ("Where are bakeries scarce?")
ESSENTIAL_PLURALS = {
    "Bakery": "bakeries",
    "Pharmacy": "pharmacies",
    "Supermarket": "supermarkets",
    "Convenience store": "convenience stores",
    "Butcher": "butchers",
    "Greengrocer": "greengrocers",
    "Post office": "post offices",
    "Fuel station": "fuel stations",
}

# Reverse lookup: OSM type -> essential category
TYPE_TO_ESSENTIAL = {t: cat for cat, types in ESSENTIAL_CATEGORIES.items() for t in types}

# ---------------------------------------------------------------------------
# Grocery retail brands (part 2)
# ---------------------------------------------------------------------------
# OSM types counted as "general grocery retail"
FOOD_RETAIL_TYPES = ["supermarket", "convenience"]

# Store formats, to compare brands like for like:
# a hypermarket and a 100 m² convenience store should not weigh the same.
STORE_FORMATS = {
    "Supermarkets & hypermarkets": ["supermarket"],
    "Convenience stores": ["convenience"],
    "All formats": FOOD_RETAIL_TYPES,
}
DEFAULT_STORE_FORMAT = "Supermarkets & hypermarkets"
DEFAULT_BRANDS = ["E.Leclerc", "Carrefour", "Intermarché"]

# Patterns (regex, case-insensitive) -> harmonised brand.
# Order matters: the first matching rule wins.
# Formats of the same brand are grouped (Carrefour City, Market, Express...).
BRAND_PATTERNS = [
    (r"leclerc", "E.Leclerc"),
    (r"intermarch", "Intermarché"),
    (r"carrefour", "Carrefour"),
    (r"^(?:super|hyper|marché)\s*u$|^u\s*express$|^utile$|syst[eè]me\s*u", "Système U"),
    (r"\bauchan\b", "Auchan"),
    (r"\blidl\b", "Lidl"),
    (r"\baldi\b", "Aldi"),
    (r"\bnetto\b", "Netto"),
    (r"monoprix|monop'", "Monoprix"),
    (r"franprix", "Franprix"),
    (r"\bcasino\b|g[ée]ant casino", "Casino"),
    (r"\bspar\b", "Spar"),
    (r"\bvival\b", "Vival"),
    (r"\bproxi\b", "Proxi"),
    (r"cocci\s*market|coccinelle", "Coccinelle / CocciMarket"),
    (r"\bcora\b", "Cora"),
    (r"\bmatch\b", "Match"),
    (r"leader price", "Leader Price"),
    (r"grand frais", "Grand Frais"),
    (r"biocoop", "Biocoop"),
    (r"picard", "Picard"),
    # --- Brands added after exploring the data (stores with no recognised brand) ---
    # Convenience chains
    (r"\bg\s*20\b", "G20"),
    (r"\b8\s*[àa]\s*huit\b", "8 à Huit"),
    (r"panier sympa", "Panier Sympa"),
    (r"votre march[ée]", "Votre Marché"),
    (r"viv[ée]co", "Viveco"),
    (r"\bsherpa\b", "Sherpa"),
    (r"[ée]pi\s*service", "Épi Service"),
    (r"^coop\b", "Coop"),
    (r"^fresh\b", "Fresh"),
    (r"march[ée] d.?\s*[àa] c[ôo]t[ée]", "Le Marché d'à côté"),
    (r"\bdiagonal\b", "Diagonal"),
    (r"\bsitis\b", "Sitis"),
    (r"\bbi1\b", "Bi1"),
    (r"douka", "Douka Bé"),
    # Discount / supermarkets
    (r"colruyt", "Colruyt"),
    (r"\bnorma\b", "Norma"),
    (r"supeco", "Supeco"),
    (r"chrono\s*drive", "Chronodrive"),
    # Organic
    (r"la vie claire", "La Vie Claire"),
    (r"naturalia", "Naturalia"),
    (r"bio\s*c.?\s*bon", "Bio c' Bon"),
    (r"comptoirs? de la bio", "Les Comptoirs de la Bio"),
    (r"\bso\.?\s*bio\b", "So.bio"),
    (r"biomonde", "Biomonde"),
    (r"satoriz", "Satoriz"),
    # Fuel-station shops ("Bonjour" = TotalEnergies station shops)
    (r"^total(?:\s*energies)?$|^bonjour$|shell select|^esso\b|^avia\b|^bp\b", "Fuel-station shop"),
]
# NB: "Alimentation générale", "Épicerie", "Duka" (= "shop" in Mayotte)... are generic names of
# independent shops: they are deliberately left without a brand.

# Names that must NOT be read as a brand (fallback on the "name" column)
# e.g. "Épicerie du Carrefour" = a crossroads ("carrefour" in French), not the brand.
NAME_EXCLUSIONS = r"\b(?:du|des|au|aux)\s+carrefours?\b"

# Labels for stores without a recognised brand / outside the top N
NO_BRAND_LABEL = "No identified brand"
OTHER_BRANDS_LABEL = "Other brands"

# ---------------------------------------------------------------------------
# Data freshness (pd.cut, like the size classes in the trees lab)
# ---------------------------------------------------------------------------
# Time since the last OSM edit, in years
FRESHNESS_BINS = [0, 1, 3, 5, float("inf")]
FRESHNESS_LABELS = ["< 1 year", "1-3 years", "3-5 years", "> 5 years"]

# ---------------------------------------------------------------------------
# Maps 
# ---------------------------------------------------------------------------
MAP_CENTER_METRO = {"lat": 46.6, "lon": 2.4}
MAP_ZOOM_METRO = 4.6
MAP_STYLE = "carto-positron"
MAP_SAMPLE_SIZE = 20_000   # max number of points drawn on a map (keeps it smooth)
