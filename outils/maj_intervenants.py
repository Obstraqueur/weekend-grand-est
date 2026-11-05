"""Met à jour la liste des intervenants dans une page d'orga (constante INTERV).

Usage : python3 maj_intervenants.py intervenants.json page1.html [page2.html ...]

intervenants.json : soumissions du formulaire Jotform 263074696052057 (« Orateurs et intervenants »),
[{"id": "...", "date": "2026-11-05 10:00:00", "prenom": "...", "nom": "...", "eglise": "...",
  "roles": "Prédication, Atelier" (texte des cases cochées), "atelier": "titre ou vide",
  "presence": "Vendredi soir, Samedi matin + midi" (texte des cases cochées),
  "logement": "Oui" | "Non", "allergies": "texte", "materiel": "texte"}]

Pas d'e-mail ni de téléphone dans la page. Allergies : seulement oui/non.
Si une personne a répondu deux fois (même prénom + nom), seule la réponse la plus récente compte.
"""
import json, re, sys, unicodedata, datetime

MOMENTS = ["Vendredi soir", "Samedi matin + midi", "Samedi midi + après-midi",
           "Samedi après-midi + dîner", "Samedi dîner + soirée louange", "Dimanche matin + midi"]

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

subs = json.load(open(sys.argv[1], encoding="utf-8"))
latest = {}
for s in subs:
    if "TEST" in (s.get("prenom", "") + s.get("nom", "")).upper():
        continue
    k = norm(s.get("prenom", "") + " " + s.get("nom", ""))
    if k and (k not in latest or int(s["id"]) > int(latest[k]["id"])):
        latest[k] = s

rows = []
for s in sorted(latest.values(), key=lambda s: int(s["id"])):
    roles, pres = norm(s.get("roles")), norm(s.get("presence"))
    rows.append({
        "id": str(s["id"]), "d": (s.get("date") or "")[:10],
        "n": ((s.get("prenom") or "").strip() + " " + (s.get("nom") or "").strip()).strip(),
        "e": (s.get("eglise") or "").strip(),
        "r": [int("predication" in roles), int("atelier" in roles), int("temoignage" in roles)],
        "at": (s.get("atelier") or "").strip(),
        "pr": [int(norm(m) in pres) for m in MOMENTS],
        "lg": 1 if (s.get("logement") or "").lower().startswith("oui") else 0,
        "al": 1 if (s.get("allergies") or "").strip().lower() not in ("", "-", "non", "aucune", "ras", "rien") else 0,
        "mat": (s.get("materiel") or "").strip()[:140],
    })

mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))
data = {"updated": f"{now.day} {mois[now.month-1]} {now:%Hh%M}", "list": rows}
for path in sys.argv[2:]:
    html = open(path, encoding="utf-8").read()
    old = json.loads(re.search(r"^const INTERV=(\{.*\});$", html, re.M).group(1))
    changed = old.get("list") != rows
    if changed:
        html = re.sub(r"^const INTERV=\{.*\};$", lambda m: "const INTERV=" + json.dumps(data, ensure_ascii=False) + ";", html, count=1, flags=re.M)
        open(path, "w", encoding="utf-8").write(html)
    print(json.dumps({"page": path, "changed": changed, "intervenants": len(rows)}, ensure_ascii=False))
