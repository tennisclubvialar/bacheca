#!/usr/bin/env python3
"""Torneo Sociale 2026-27: crea live/sociale.json per la bacheca.

Uso: python3 scripts/sociale.py dump.json
dump.json = {"tornei": [documenti della collection tournaments dell'app Tornei circolo],
             "giocatori": {id: nome}}
Le date (chiusura iscrizioni, partenza, fine prevista) sono quelle del calendario ufficiale
qui sotto; dall'app si prendono solo gli iscritti.
"""
import json, sys, datetime

CAL = [  # nome nell'app, nome in bacheca, tipo, colore, bollino, sottobollino, chiusura, partenza, fine prevista, quota
    ("Open Maschile",           "Open Maschile",           "Singolare", "#9aa8ff", "OPEN",  "UOMINI", "2026-11-23", "2026-11-28", "2026-12-20", 30),
    ("Over 50 Maschile",        "Over 50 Maschile",        "Singolare", "#5cc8ff", "50+",   "UOMINI", "2026-12-14", "2026-12-19", "2027-01-17", 30),
    ("Over 60 Maschile",        "Over 60 Maschile",        "Singolare", "#6ef0bd", "60+",   "UOMINI", "2027-01-11", "2027-01-16", "2027-02-07", 30),
    ("Doppio Maschile",         "Doppio Maschile Open",    "Doppio",    "#9aa8ff", "OPEN",  "DOPPIO", "2027-02-01", "2027-02-06", "2027-02-28", 15),
    ("Doppio Over 60 Maschile", "Doppio Over 60 Maschile", "Doppio",    "#6ef0bd", "60+",   "DOPPIO", "2027-02-22", "2027-02-27", "2027-03-14", 15),
    ("Doppio Femminile",        "Doppio Femminile Open",   "Doppio",    "#ff8fcb", "OPEN",  "DOPPIO", "2027-02-22", "2027-02-27", "2027-03-14", 15),
    ("Open Femminile",          "Open Femminile",          "Singolare", "#ff8fcb", "OPEN",  "DONNE",  "2027-03-08", "2027-03-13", "2027-03-28", 30),
]

def breve(nome):
    """'Mario Rossi' -> 'Rossi M.' (cognome e iniziale del nome)"""
    p = (nome or "").split()
    if len(p) < 2: return nome or ""
    return " ".join(p[1:]) + " " + p[0][0] + "."

def main(path):
    d = json.load(open(path))
    gioc = d.get("giocatori", {})
    tornei = {}
    for t in d.get("tornei", []):
        data = t.get("data", t)
        nome = data.get("name", "").replace("Torneo Sociale · ", "").strip()
        tornei[nome] = data
    out = {"aggiornato": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime("%d/%m %H:%M"), "finali": "2027-04-04", "categorie": []}
    for app, nome, tipo, col, bt, bs, chiusura, partenza, fine, quota in CAL:
        t = tornei.get(app, {})
        ent = t.get("entrants", {}) or {}
        iscritti = []
        for pid, v in ent.items():
            if not v: continue
            if isinstance(v, dict) and v.get("partner"):   # coppia
                iscritti.append(breve(gioc.get(pid, "")) + " / " + breve(gioc.get(v["partner"], "")))
            else:
                iscritti.append(breve(gioc.get(pid, pid)))
        iscritti = sorted(x for x in iscritti if x.strip())
        out["categorie"].append({"nome": nome, "tipo": tipo, "colore": col, "bt": bt, "bs": bs, "chiusura": chiusura,
                                 "partenza": partenza, "fine": fine, "quota": quota, "iscritti": iscritti})
    out["categorie"].sort(key=lambda c: (c["chiusura"], c["nome"]))
    json.dump(out, open("live/sociale.json", "w"), ensure_ascii=False, indent=1)
    print("ok", sum(len(c["iscritti"]) for c in out["categorie"]), "iscritti")

if __name__ == "__main__":
    main(sys.argv[1])
