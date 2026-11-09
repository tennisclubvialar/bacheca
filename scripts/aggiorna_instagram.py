"""Scarica gli ultimi post del profilo Instagram del circolo e li salva per la bacheca.

Usa il collegamento ufficiale di Instagram (API con Instagram Login).
Il token di accesso arriva dalla variabile d'ambiente IG_TOKEN (segreto di GitHub).
"""
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v22.0/me/media"
QUANTI = 12
CARTELLA = pathlib.Path(__file__).resolve().parent.parent / "instagram"


def scarica(url, dest=None):
    req = urllib.request.Request(url, headers={"User-Agent": "bacheca-tcvialar"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if dest:
        dest.write_bytes(data)
    return data


def main():
    token = os.environ.get("IG_TOKEN")
    if not token:
        sys.exit("Manca il segreto IG_TOKEN")
    campi = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
    url = f"{API}?{urllib.parse.urlencode({'fields': campi, 'limit': QUANTI, 'access_token': token})}"
    risposta = json.loads(scarica(url))
    if "error" in risposta:
        sys.exit(f"Errore Instagram: {risposta['error']}")

    CARTELLA.mkdir(exist_ok=True)
    posts, tenuti = [], set()
    for m in risposta.get("data", []):
        img = m.get("thumbnail_url") if m.get("media_type") == "VIDEO" else m.get("media_url")
        if not img:
            continue
        nome = f"{m['id']}.jpg"
        dest = CARTELLA / nome
        if not dest.exists():
            try:
                scarica(img, dest)
            except Exception as e:  # un'immagine non scaricabile non blocca le altre
                print(f"Salto {m['id']}: {e}")
                continue
        tenuti.add(nome)
        posts.append({
            "id": m["id"],
            "image": f"instagram/{nome}",
            "caption": m.get("caption", ""),
            "type": m.get("media_type"),
            "permalink": m.get("permalink"),
            "timestamp": m.get("timestamp"),
        })

    for f in CARTELLA.glob("*.jpg"):
        if f.name not in tenuti:
            f.unlink()

    out = CARTELLA / "posts.json"
    nuovo = json.dumps({"posts": posts}, ensure_ascii=False, indent=2)
    if not out.exists() or out.read_text(encoding="utf-8") != nuovo:
        out.write_text(nuovo, encoding="utf-8")
        print(f"Aggiornati {len(posts)} post")
    else:
        print("Nessun post nuovo")


if __name__ == "__main__":
    main()
