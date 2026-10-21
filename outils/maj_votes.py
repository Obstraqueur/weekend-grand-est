"""Met à jour le classement des ateliers dans une page (index.html de l'orga).

Usage : python3 maj_votes.py votes.json page1.html [page2.html ...]
votes.json : liste de soumissions [{"id": "...", "nom": "Prénom Nom", "ateliers": ["titre exact", ...]}, ...]
Une seule voix par personne : on garde sa soumission la plus récente (id Jotform le plus grand).
"""
import json, re, sys, unicodedata, datetime

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

subs = json.load(open(sys.argv[1], encoding="utf-8"))
latest = {}
for s in subs:
    k = norm(s["nom"])
    if k not in latest or int(s["id"]) > int(latest[k]["id"]):
        latest[k] = s
mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
stamp = f"{now.day} {mois[now.month-1]} {now:%Hh%M}"
for path in sys.argv[2:]:
    html = open(path, encoding="utf-8").read()
    at = json.loads(re.search(r"const ATELIERS=(\[.*?\]);", html, re.S).group(1))
    ids = {norm(a["t"]): a["id"] for a in at}
    counts, voters, inconnus = {}, [], []
    for s in sorted(latest.values(), key=lambda s: int(s["id"])):
        voters.append(" ".join(w[:1].upper() + w[1:] for w in s["nom"].split()))
        for t in s["ateliers"]:
            i = ids.get(norm(t))
            if i: counts[i] = counts.get(i, 0) + 1
            else: inconnus.append(t)
    votes = {"updated": stamp, "voters": voters, "counts": counts}
    new = re.sub(r"const VOTES=\{.*?\};", lambda m: "const VOTES=" + json.dumps(votes, ensure_ascii=False) + ";", html, count=1, flags=re.S)
    old_counts = re.search(r"const VOTES=(\{.*?\});", html, re.S).group(1)
    changed = json.loads(old_counts).get("counts") != counts or json.loads(old_counts).get("voters") != voters
    if changed:
        open(path, "w", encoding="utf-8").write(new)
    print(json.dumps({"page": path, "changed": changed, "votants": voters, "inconnus": inconnus}, ensure_ascii=False))
