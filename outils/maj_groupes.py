"""Met à jour inscription/groupes.json (liste publique des groupes déjà inscrits).

Usage : python3 maj_groupes.py groupes_soumissions.json inscription/groupes.json
groupes_soumissions.json : [{"id": "...", "type": "Nouveau groupe" | "Ajout à un groupe",
                             "nom": "...", "code": "...", "ville": "...", "prenoms": "un prénom par ligne"}, ...]
La liste publique ne contient que le code, le nom, la ville et le nombre de prénoms (pas les prénoms).
Les groupes dont le nom contient « TEST » sont ignorés.
"""
import json, sys

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

out = sorted(({"code": g["code"], "nom": g["nom"], "ville": g["ville"], "n": len(g["prenoms"])} for g in groupes.values()),
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
