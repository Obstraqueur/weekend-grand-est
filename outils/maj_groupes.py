"""Met à jour inscription/groupes.json (liste publique des groupes déjà inscrits).

Usage : python3 maj_groupes.py groupes_soumissions.json inscription/groupes.json
groupes_soumissions.json : [{"id": "...", "type": "Nouveau groupe" | "Ajout à un groupe",
                             "nom": "...", "code": "...", "ville": "...", "prenoms": "un prénom par ligne"}, ...]
La liste publique ne contient que le code, le nom, la ville et le nombre de prénoms (pas les prénoms).
Les groupes dont le nom contient « TEST » sont ignorés.
"""
import json, os, re, sys, unicodedata

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

_a = os.path.join(os.path.dirname(os.path.abspath(__file__)), "groupes_alias.json")
ALIAS = {norm(k): v for k, v in json.load(open(_a, encoding="utf-8")).items() if not k.startswith("_")} if os.path.exists(_a) else {}

subs = json.load(open(sys.argv[1], encoding="utf-8"))
groupes = {}
for s in sorted(subs, key=lambda s: int(s.get("id") or 0)):
    code, nom = (s.get("code") or "").strip(), (s.get("nom") or "").strip()
    if not code or not nom or "TEST" in nom.upper():
        continue
    prenoms = [p.strip() for p in str(s.get("prenoms") or "").splitlines() if p.strip()]
    g = groupes.setdefault(code, {"code": code, "nom": nom, "ville": (s.get("ville") or "").strip(), "prenoms": []})
    if s.get("type", "").startswith("Nouveau"):
        g["nom"] = nom
        g["ville"] = (s.get("ville") or g["ville"]).strip()
    g["prenoms"] += [p for p in prenoms if p not in g["prenoms"]]

out = sorted(({"code": g["code"], "nom": ALIAS.get(norm(g["nom"]), g["nom"]), "ville": g["ville"], "n": len(g["prenoms"])} for g in groupes.values()),
             key=lambda g: g["nom"].lower())
path = sys.argv[2]
try:
    old = json.load(open(path, encoding="utf-8"))
except Exception:
    old = None
changed = old != out
if changed:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps({"changed": changed, "groupes": len(out)}, ensure_ascii=False))
