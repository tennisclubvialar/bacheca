#!/usr/bin/env python3
"""Converte i dati del torneo (dall'artefatto Rodeo Circolo) nel file live/torneo.json letto dalla bacheca.
Uso: python3 scripts/live_torneo.py dump.json   (dump = {"torneo": {...data...}, "giocatori": {id: nome}, "news": [...]})"""
import json, sys, datetime
d = json.load(open(sys.argv[1]))
T, P = d["torneo"], d["giocatori"]
news = d.get("news", [])
def nome(pid):
    n = P.get(pid, "?").strip().split()
    return (" ".join(n[1:]) + " " + n[0][0] + ".") if len(n) >= 2 else (n[0] if n else "?")   # cognome + iniziale del nome
LET = "ABCDEFGH"
groupOf = T.get("groupOf", {}) or {}
M = T.get("matches", {}) or {}
G = T.get("groupCount") or (max(groupOf.values()) + 1 if groupOf else 0)
def score(m): return " ".join(f"{a}-{b}" for a, b in (m.get("sets") or []))
def winner(m):
    s = m.get("sets") or []
    wa = sum(1 for a, b in s if a > b); wb = sum(1 for a, b in s if b > a)
    return "a" if wa > wb else "b" if wb > wa else None
# classifiche gironi
gironi = []
for g in range(G):
    ids = [p for p, gg in groupOf.items() if gg == g]
    st = {p: dict(id=p, n=nome(p), g=0, v=0, gf=0, gs=0) for p in ids}
    tot = done = 0
    for k, m in M.items():
        if m.get("stage") != "group" or m.get("g") != g: continue
        tot += 1
        if not m.get("done"): continue
        done += 1
        a, b = m["a"][2:], m["b"][2:]
        if a not in st or b not in st: continue
        st[a]["g"] += 1; st[b]["g"] += 1
        for x, y in m.get("sets") or []:
            st[a]["gf"] += x; st[a]["gs"] += y; st[b]["gf"] += y; st[b]["gs"] += x
        w = winner(m)
        if w == "a": st[a]["v"] += 1
        elif w == "b": st[b]["v"] += 1
    rows = sorted(st.values(), key=lambda r: (-r["v"], -(r["gf"] - r["gs"]), -r["gf"], r["n"]))
    gironi.append(dict(nome="Girone " + LET[g], completo=(tot > 0 and done == tot), righe=[dict(n=r["n"], g=r["g"], v=r["v"], diff=r["gf"] - r["gs"]) for r in rows], _ids=[r["id"] for r in rows]))
def risolvi(ref):
    if not ref or ref == "-": return "riposo"
    t, _, rest = ref.partition(":")
    if t == "p": return nome(rest)
    if t == "o":
        g, pos = map(int, rest.split(":"))
        gi = gironi[g] if g < len(gironi) else None
        if gi and gi["completo"] and pos < len(gi["_ids"]): return nome(gi["_ids"][pos])
        return f"{pos+1}° Girone {LET[g]}"
    if t in ("w", "l"):
        m = M.get(rest)
        if m and m.get("done"):
            w = winner(m)
            if w: return risolvi(m["a"] if (w == "a") == (t == "w") else m["b"])
        return ("Vincente " if t == "w" else "Perdente ") + rest.split("-")[-1]
    return ref
FASE = {"group": "Girone", "main": "Tabellone principale", "cons": "Consolazione"}
def etichetta(k, m):
    st = m.get("stage")
    if st == "group": return "Girone " + LET[m.get("g", 0)]
    rds = [x.get("rd", 1) for x in M.values() if x.get("stage") == st]
    mx = max(rds) if rds else 1
    rd = m.get("rd", 1)
    nome_r = "Finale" if rd == mx else "Semifinale" if rd == mx - 1 else f"Turno {rd}"
    return ("Consolazione · " if st == "cons" else "") + nome_r
ordine = {"group": 0, "main": 1, "cons": 1}
partite = sorted(M.items(), key=lambda kv: (ordine.get(kv[1].get("stage"), 2), kv[1].get("rd", 0), kv[0]))
risultati, prossime = [], []
for k, m in partite:
    a, b = risolvi(m.get("a")), risolvi(m.get("b"))
    if "riposo" in (a, b): continue
    r = dict(fase=etichetta(k, m), a=a, b=b, campo=m.get("court"))
    if m.get("done"):
        w = winner(m); r.update(score=score(m), vince=w); risultati.append(r)
    else:
        prossime.append(r)
risultati = risultati[::-1][:8]
prossime = prossime[:6]
def tabellone(stage):
    out = []
    for k, m in partite:
        if m.get("stage") != stage: continue
        a, b = risolvi(m.get("a")), risolvi(m.get("b"))
        out.append(dict(fase=etichetta(k, m), a=a, b=b, score=score(m) if m.get("done") else "", vince=winner(m) if m.get("done") else None))
    return out
finali = dict(principale=tabellone("main"), consolazione=tabellone("cons"))
campioni = {}
for key, lst in (("principale", finali["principale"]), ("consolazione", finali["consolazione"])):
    if lst and lst[-1]["fase"].endswith("Finale") and lst[-1]["vince"]:
        campioni[key] = lst[-1]["a"] if lst[-1]["vince"] == "a" else lst[-1]["b"]
iscritti = sorted(nome(p) for p, ok in (T.get("entrants") or {}).items() if ok)
for g in gironi: g.pop("_ids")
out = dict(
    attivo=True, aggiornato=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime("%H:%M"),
    data=T.get("date"), nome=d.get("titolo") or T.get("name"), stato=T.get("status"),
    posti=dict(iscritti=len(iscritti), max=T.get("max")), iscritti=iscritti,
    gironi=gironi, risultati=risultati, prossime=prossime, finali=finali, campioni=campioni, news=news)
json.dump(out, open(d.get("out", "live/torneo.json"), "w"), ensure_ascii=False, indent=1)
print("ok", out["stato"], len(iscritti), "iscritti", len(risultati), "risultati")
