"""Met à jour les choix d'ateliers des participants dans une page d'orga (constante CHOIX).

Usage : python3 maj_choix.py choix.json page1.html [page2.html ...]

choix.json : soumissions du formulaire Jotform 263234224375050 « Choix des ateliers » :
[{"id": "...", "prenom": "...", "choix1": "titre de l'atelier", "choix2": "titre de l'atelier"}]
Si une personne a répondu deux fois (même prénom), seule la réponse la plus récente compte.
Les réponses dont le prénom contient « TEST » sont ignorées.
"""
import json, re, sys, unicodedata, datetime

ATELIERS = ["Choisir le pardon pour avancer", "Servir Dieu : par où ou par quoi commencer ?",
            "Avancer dans les épreuves", "Comment le célibat aide-t-il à cheminer avec Dieu ?",
            "Avancer avec Dieu grâce à la prière et la lecture de la Bible",
            "La communion fraternelle est-elle une nécessité ou une option ?"]

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

IDX = {norm(t): i + 1 for i, t in enumerate(ATELIERS)}
def num(t):
    t = norm(t)
    if t in IDX: return IDX[t]
    for k, v in IDX.items():
        if k[:25] and (k[:25] in t or t[:25] in k): return v
    return 0

subs = json.load(open(sys.argv[1], encoding="utf-8"))
latest = {}
for s in subs:
    p = (s.get("prenom") or "").strip()
    if not p or "TEST" in p.upper(): continue
    k = norm(p)
    if k not in latest or int(s["id"]) > int(latest[k]["id"]): latest[k] = s
rows = [{"id": str(s["id"]), "n": " ".join(w[:1].upper() + w[1:] for w in s["prenom"].strip().split()),
         "c1": num(s.get("choix1")), "c2": num(s.get("choix2"))}
        for s in sorted(latest.values(), key=lambda s: int(s["id"]))]
mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1)))
data = {"updated": f"{now.day} {mois[now.month-1]} {now:%Hh%M}", "list": rows}
for path in sys.argv[2:]:
    html = open(path, encoding="utf-8").read()
    old = json.loads(re.search(r"^const CHOIX=(\{.*\});$", html, re.M).group(1))
    changed = old.get("list") != rows
    if changed:
        html = re.sub(r"^const CHOIX=\{.*\};$", lambda m: "const CHOIX=" + json.dumps(data, ensure_ascii=False) + ";", html, count=1, flags=re.M)
        open(path, "w", encoding="utf-8").write(html)
    print(json.dumps({"page": path, "changed": changed, "reponses": len(rows)}, ensure_ascii=False))
