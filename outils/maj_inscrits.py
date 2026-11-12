"""Met à jour le tableau des inscriptions dans une page d'orga (constante INSCRITS).

Usage : python3 maj_inscrits.py inscrits.json page1.html [page2.html ...]

inscrits.json : liste des soumissions du formulaire d'inscription Jotform 262846622284059,
une entrée par soumission, avec les réponses en texte :
[{"id": "...", "date": "2026-10-27 18:02:11", "prenom": "...", "nom": "...", "ville": "Metz",
  "statut": "Étudiant(e) ..." | "Vie active ...", "groupe": "GBU Nancy (gbu-nancy-ab12)" | "",
  "arrivee": "Vendredi ..." | "Samedi ...", "paiement": "Virement" | "Sur place à l'accueil",
  "paye": "Oui" | "Pas encore", "voiture": "Oui" | "Non", "places": "3", "covoiturage": "...",
  "allergies": "texte libre ou vide", "logement": "Oui" | "Non"}]

Champs facultatifs en plus : "covoiturage", "places_proposees", "don", "remarque".
La page montre le détail complet des réponses (nom complet, allergies, covoiturage, don, remarque),
mais jamais d'e-mail, de téléphone, d'adresse ni de date de naissance : ceux-là restent dans Jotform.
Si une personne s'est inscrite deux fois (même prénom + nom), seule la soumission la plus récente compte.
"""
import json, re, sys, unicodedata, datetime

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

subs = json.load(open(sys.argv[1], encoding="utf-8"))
# Corrections manuelles : prénoms + noms des personnes qui ont un logement sur Metz même si Jotform ne le dit pas.
import os
_f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logement_metz.json")
LOGES = {norm(n) for n in json.load(open(_f, encoding="utf-8"))} if os.path.exists(_f) else set()
latest = {}
for s in subs:
    if "TEST" in (s.get("prenom", "") + s.get("nom", "")).upper():
        continue
    k = norm(s.get("prenom", "") + " " + s.get("nom", ""))
    if not k:
        continue
    if k not in latest or int(s["id"]) > int(latest[k]["id"]):
        latest[k] = s

def code_groupe(g):
    m = re.search(r"\(([^()]+)\)\s*$", g or "")
    return m.group(1).strip() if m else nom_groupe(g)

_a = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groupes_alias.json")
ALIAS = {norm(k): v for k, v in json.load(open(_a, encoding="utf-8")).items() if not k.startswith("_")} if os.path.exists(_a) else {}

def nom_groupe(g):
    n = re.sub(r"\s*\([^()]*\)\s*$", "", g or "").strip()
    return ALIAS.get(norm(n), n)

rows = []
for s in sorted(latest.values(), key=lambda s: int(s["id"])):
    nom = (s.get("nom") or "").strip()
    places = re.sub(r"[^0-9]", "", str(s.get("places") or ""))
    rows.append({
        "id": str(s["id"]),
        "d": (s.get("date") or "")[:10],
        "n": ((s.get("prenom") or "").strip().title() + (" " + nom[:1].upper() + "." if nom else "")).strip(),
        "v": (s.get("ville") or "").strip(),
        "a": "actif" if "vie active" in (s.get("statut") or "").lower() else "etu",
        "g": nom_groupe(s.get("groupe")), "gc": code_groupe(s.get("groupe")),
        "j": "sam" if (s.get("arrivee") or "").lower().startswith("samedi") else "ven",
        "p": "oui" if (s.get("paye") or "").lower().startswith("oui") else "non",
        "m": "virement" if "virement" in (s.get("paiement") or "").lower() else "place",
        "c": int(places) if (s.get("voiture") or "").lower().startswith("oui") and places else 0,
        "lg": 1 if (s.get("logement") or "").lower().startswith("oui") or norm(s.get("prenom", "") + " " + s.get("nom", "")) in LOGES else 0,
        "al": 1 if (s.get("allergies") or "").strip() not in ("", "-", "non", "Non", "aucune", "Aucune", "RAS") else 0,
        # Détail complet des réponses (sans e-mail, téléphone, adresse ni date de naissance)
        "nf": " ".join(w[:1].upper() + w[1:].lower() for w in ((s.get("prenom") or "").strip() + " " + nom).split()),
        "alt": (s.get("allergies") or "").strip(),
        "cov": (s.get("covoiturage") or "").strip(),
        "cp": re.sub(r"[^0-9]", "", str(s.get("places_proposees") or "")),
        "don": re.sub(r"[^0-9,.]", "", str(s.get("don") or "")),
        "rq": (s.get("remarque") or "").strip(),
    })

# Un groupe saisi sans code (ex. « Metz » → alias « Metzc'estmieux ») reprend le code du groupe du même nom.
codes = {}
for r in rows:
    if r["g"] and r["gc"] != r["g"]:
        codes.setdefault(norm(r["g"]), r["gc"])
for r in rows:
    if r["g"] and r["gc"] == r["g"]:
        r["gc"] = codes.get(norm(r["g"]), r["gc"])

mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))
data = {"updated": f"{now.day} {mois[now.month-1]} {now:%Hh%M}", "list": rows}
for path in sys.argv[2:]:
    html = open(path, encoding="utf-8").read()
    old = json.loads(re.search(r"^const INSCRITS=(\{.*\});$", html, re.M).group(1))
    changed = old.get("list") != rows
    if changed:
        new = re.sub(r"^const INSCRITS=\{.*\};$", lambda m: "const INSCRITS=" + json.dumps(data, ensure_ascii=False) + ";", html, count=1, flags=re.M)
        open(path, "w", encoding="utf-8").write(new)
    print(json.dumps({"page": path, "changed": changed, "inscrits": len(rows)}, ensure_ascii=False))
