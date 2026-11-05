"""
Forevers achievements ur Blizzards statiska API: namn, beskrivning, kategori, poäng, belöning och ikon.

  python scripts/ach_static.py

Skriver data/forever/achievements.json, data/forever/professions.json (yrke → ikon) och ikonerna till data/forever/ach-icons/<file_data_id>.jpg.
Ändras bara med en ny patch, så det körs för hand och läggs i repot (build_hemmet.py läser det).
Samma achievement finns ofta en gång per faktion med olika id. De slås ihop på namnet.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_hemmet as f

NS = "static-forever-eu"
OUT = f.ROOT / "data" / "forever"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    f.TOKEN = f.token()
    (OUT / "ach-icons").mkdir(parents=True, exist_ok=True)
    cats = f.get("/data/wow/achievement-category/index", NS)["categories"]
    with ThreadPoolExecutor(8) as ex:
        cat = {c["id"]: c for c in ex.map(lambda c: f.get(f"/data/wow/achievement-category/{c['id']}", NS), cats)}
    ids = [a["id"] for a in f.get("/data/wow/achievement/index", NS)["achievements"]]
    with ThreadPoolExecutor(8) as ex:
        details = list(ex.map(lambda i: f.get(f"/data/wow/achievement/{i}", NS), ids))
        media = list(ex.map(lambda i: f.get(f"/data/wow/media/achievement/{i}", NS) or {}, ids))
    out = {}
    for d, m in zip(details, media):
        icon = next((a for a in m.get("assets", []) if a["key"] == "icon"), None)
        c = cat.get(d["category"]["id"], {})
        parent = (c.get("parent_category") or {}).get("name")
        a = out.setdefault(d["name"], {
            "ids": [], "desc": d.get("description"), "pts": d.get("points", 0), "reward": d.get("reward_description"),
            "cat": parent or d["category"]["name"], "sub": d["category"]["name"] if parent else None,
            "order": d.get("display_order", 0), "icon": icon and icon["file_data_id"],
        })
        a["ids"].append(d["id"])
        if icon:
            f.download(icon["value"], OUT / "ach-icons" / f"{icon['file_data_id']}.jpg")
    profs = {}
    for p in f.get("/data/wow/profession/index", NS)["professions"]:
        icon = next((a for a in (f.get(f"/data/wow/media/profession/{p['id']}", NS) or {}).get("assets", []) if a["key"] == "icon"), None)
        if icon and "[DNT]" not in p["name"]:
            profs[p["name"]] = icon["file_data_id"]
            f.download(icon["value"], OUT / "ach-icons" / f"{icon['file_data_id']}.jpg")
    (OUT / "professions.json").write_text(json.dumps(profs, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "achievements.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} achievements ({len(ids)} id) i {len({a['cat'] for a in out.values()})} kategorier")


if __name__ == "__main__":
    main()
