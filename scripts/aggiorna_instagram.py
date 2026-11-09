"""Scarica gli ultimi post del profilo Instagram del circolo e li salva per la bacheca.

Due sorgenti possibili (si usa la prima configurata):
- BEHOLD_FEED_URL: indirizzo del feed JSON di Behold (behold.so), collegato a @tennisclubvialar
- IG_TOKEN: token del collegamento ufficiale di Instagram (API con Instagram Login)
"""
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

QUANTI = 12
CARTELLA = pathlib.Path(__file__).resolve().parent.parent / "instagram"


def scarica(url, dest=None):
    req = urllib.request.Request(url, headers={"User-Agent": "bacheca-tcvialar"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if dest:
        dest.write_bytes(data)
    return data


def da_behold(url):
    feed = json.loads(scarica(url))
    for p in feed.get("posts", []):
        sizes = p.get("sizes") or {}
        img = None
        for k in ("large", "full", "medium"):
            img = (sizes.get(k) or {}).get("mediaUrl")
            if img:
                break
        if not img:
            img = p.get("thumbnailUrl") if p.get("mediaType") == "VIDEO" else p.get("mediaUrl")
        yield {
            "id": str(p.get("id")),
            "img": img,
            "caption": p.get("caption") or p.get("prunedCaption") or "",
            "type": p.get("mediaType"),
            "permalink": p.get("permalink"),
            "timestamp": p.get("timestamp"),
        }


def da_instagram(token):
    campi = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
    url = "https://graph.instagram.com/v22.0/me/media?" + urllib.parse.urlencode(
        {"fields": campi, "limit": QUANTI, "access_token": token})
    risposta = json.loads(scarica(url))
    if "error" in risposta:
        sys.exit(f"Errore Instagram: {risposta['error']}")
    for m in risposta.get("data", []):
        yield {
            "id": m["id"],
            "img": m.get("thumbnail_url") if m.get("media_type") == "VIDEO" else m.get("media_url"),
            "caption": m.get("caption", ""),
            "type": m.get("media_type"),
            "permalink": m.get("permalink"),
            "timestamp": m.get("timestamp"),
        }


def main():
    if os.environ.get("BEHOLD_FEED_URL"):
        sorgente = da_behold(os.environ["BEHOLD_FEED_URL"])
    elif os.environ.get("IG_TOKEN"):
        sorgente = da_instagram(os.environ["IG_TOKEN"])
    else:
        sys.exit("Nessuna sorgente configurata: imposta BEHOLD_FEED_URL o IG_TOKEN")

    CARTELLA.mkdir(exist_ok=True)
    posts, tenuti = [], set()
    for m in sorgente:
        if not m["img"] or len(posts) >= QUANTI:
            continue
        nome = f"{m['id']}.jpg"
        dest = CARTELLA / nome
        if not dest.exists():
            try:
                scarica(m["img"], dest)
            except Exception as e:  # un'immagine non scaricabile non blocca le altre
                print(f"Salto {m['id']}: {e}")
                continue
        tenuti.add(nome)
        posts.append({"id": m["id"], "image": f"instagram/{nome}", "caption": m["caption"],
                      "type": m["type"], "permalink": m["permalink"], "timestamp": m["timestamp"]})

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
