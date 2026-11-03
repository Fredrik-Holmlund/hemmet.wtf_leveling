"""
Sammanfattar de senaste 7 dagarna till dist/veckan.txt, underlaget till veckobrevet.

  python scripts/veckan.py --src data/hemmet

Publiceras på resan.hemmet.wtf/veckan.txt vid varje bygge, så att en AI kan läsa den därifrån.
Bara fakta, ingen text i guildens röst. Körs efter build_dist.py, som tömmer dist/.
"""
import argparse
import collections
import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Europe/Stockholm")
DAG = 86_400_000
MAX_LEVEL = 60


def tid(t):
    return datetime.datetime.fromtimestamp(t / 1000, TZ).strftime("%Y-%m-%d %H:%M")


def lista(rader):
    return [f"- {r}" for r in rader] or ["- Inget"]


def levels(events, fran, till, start):
    """Levels per karaktär mellan fran och till. Bygger på dings, så en karaktär som hoppat över en hämtning räknas rätt."""
    forst, sist = {}, {}
    for e in events:
        if e["k"] != "level":
            continue
        if e["t"] < fran:
            forst[e["n"]] = e["v"]
        elif e["t"] < till:
            forst.setdefault(e["n"], start.get(e["n"], {}).get("level", e["v"] - 1))
            sist[e["n"]] = e["v"]
    return collections.Counter({n: v - forst[n] for n, v in sist.items() if v > forst[n]})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="data/hc")
    src = ROOT / p.parse_args().src

    data = json.loads((src / "members.json").read_text(encoding="utf-8"))
    members = data["members"]
    events = sorted((json.loads(r) for r in (src / "events.jsonl").read_text(encoding="utf-8").splitlines() if r.strip()), key=lambda e: e["t"])
    now = int(datetime.datetime.now(TZ).timestamp() * 1000)
    fran = now - 7 * DAG

    snaps = sorted((src / "snapshots").glob("*.json"))

    def snapshot(t):
        """Senaste dagssnapshoten före t, annars den äldsta."""
        dag = datetime.datetime.fromtimestamp(t / 1000, TZ).strftime("%Y-%m-%d")
        return next((f for f in reversed(snaps) if f.stem <= dag), snaps[0])

    fil = snapshot(fran)
    start = json.loads(fil.read_text(encoding="utf-8"))

    denna = levels(events, fran, now, start)
    forra = levels(events, fran - 7 * DAG, fran, json.loads(snapshot(fran - 7 * DAG).read_text(encoding="utf-8")))
    period = [e for e in events if e["t"] >= fran]
    lvl = {m["name"]: m["level"] for m in members}

    # Milstolpar: första i guilden till varje tiotal, om det hände i veckan
    forst = {}
    for e in events:
        if e["k"] == "level":
            for L in range(10, MAX_LEVEL + 1, 10):
                if e["v"] >= L:
                    forst.setdefault(L, e)

    ut = [
        f"# {data['guild']}: veckan som gick",
        "",
        f"Period: {tid(fran)} till {tid(now)} svensk tid (senaste 7 dagarna).",
        f"Senast hämtat från spelet: {data['generated']} UTC.",
        "Hämtas var 30:e minut, så klockslagen är ungefärliga. Namnen står som i spelet.",
    ]
    if fil.stem > tid(fran)[:10]:
        ut.append(f"Mätningen började {fil.stem}, så perioden är kortare än en vecka.")

    ut += ["", "## Guilden just nu"]
    ut += lista([
        f"Karaktärer: {len(members)}",
        f"På level {MAX_LEVEL}: {sum(m['level'] >= MAX_LEVEL for m in members)}",
        f"Snittlevel: {sum(lvl.values()) / max(1, len(lvl)):.1f}",
        f"Inloggade under perioden: {sum((m.get('lastLogin') or 0) >= fran for m in members)}",
        "Klasser: " + ", ".join(f"{k} {v}" for k, v in collections.Counter(m["cls"] for m in members).most_common()),
    ])

    ut += ["", "## Levels"]
    ut += lista([f"Levels under perioden: {sum(denna.values())} (veckan före: {sum(forra.values())})",
                 f"Karaktärer som levlat: {len(denna)} (veckan före: {len(forra)})"])
    ut += ["", "### Flest levels"]
    ut += lista(f"{n}: +{v}, nu level {lvl.get(n, '?')}" for n, v in denna.most_common(10))

    ut += ["", f"## Nådde level {MAX_LEVEL}"]
    ut += lista(f"{e['n']}, {tid(e['t'])}" for e in period if e["k"] == "level" and e["v"] >= MAX_LEVEL)

    ut += ["", "## Först i guilden till en ny level"]
    ut += lista(f"Level {L}: {e['n']}, {tid(e['t'])}" for L, e in forst.items() if e["t"] >= fran)

    ut += ["", "## Exalted"]
    ut += lista(f"{e['n']}: {e['v']}, {tid(e['t'])}" for e in period if e["k"] == "rep")

    hk = collections.Counter()
    for e in period:
        if e["k"] == "hk":
            hk[e["n"]] += e["v"]
    ut += ["", "## Honor kills"]
    ut += lista(f"{n}: +{v}" for n, v in hk.most_common(5))

    ut += ["", "## Nya i guilden"]
    ut += lista(f"{n}, level {lvl[n]}" for n in sorted(set(lvl) - set(start)))
    ut += ["", "## Har lämnat guilden"]
    ut += lista(f"{n}, level {start[n]['level']}" for n in sorted(set(start) - set(lvl)))

    ut += ["", "## Högst item level"]
    ut += lista(f"{m['name']}: {m['ilvl']}" for m in sorted(members, key=lambda m: -(m.get("ilvl") or 0))[:5] if m.get("ilvl"))

    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "veckan.txt").write_text("\n".join(ut) + "\n", encoding="utf-8")
    print(f"Veckan klar → dist/veckan.txt ({len(period)} händelser)")


if __name__ == "__main__":
    main()
