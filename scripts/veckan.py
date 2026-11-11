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

from build_hemmet import sv   # achievementsens beskrivningar på svenska, samma som på Bedrifter

ROOT = Path(__file__).resolve().parent.parent
TZ = ZoneInfo("Europe/Stockholm")
DAG = 86_400_000
MAX_LEVEL = 60
RELEASE = "2026-11-05"   # alla började på level 1 den här dagen
FOREVER = ROOT / "data" / "forever"
# Veckans titlar ur spelstatistiken: (titel, vad som räknas, statistikrader som summeras). Samma som på Bedrifter
TITLAR = [
    ("Massmördaren", "kills som ger XP", ["Total kills that grant experience or honor"]),
    ("Needy", "need-rolls", ["Need rolls made on loot"]),
    ("Greedy", "greed-rolls", ["Greed rolls made on loot"]),
    ("Lägerelden", "camps", ["Times camped"]),
    ("Fiskekungen", "fångade fiskar", ["Fish caught"]),
    ("Apoteket", "pots, elixirs och flasks", ["Health potions consumed", "Mana potions consumed", "Elixirs consumed", "Flasks consumed"]),
    ("Hoggers bästa vän", "dödsfall", ["Total deaths"]),
    ("Hemlängtan", "hearths", ["Number of times hearthed"]),
    ("Kramgo", "kramar", ["Number of hugs"]),
    ("Questmaskinen", "klarade quests", ["Quests completed"]),
    ("Djurplågaren", "dödade critters", ["Critters killed"]),
    ("Flygaren", "flygturer", ["Flight paths taken"]),
    ("Matälskaren", "mat och dryck", ["Food eaten", "Beverages consumed"]),
]


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
    if fil.stem == RELEASE and fran < datetime.datetime.fromisoformat(RELEASE).replace(tzinfo=TZ).timestamp() * 1000:
        # Releaseveckan: hämtningen började först på morgonen, men alla började på level 1 vid midnatt
        denna = collections.Counter({m["name"]: m["level"] - 1 for m in members if m["level"] > 1})
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
    ut += lista(f"{n}: +{v}, nu level {lvl[n]}" if n in lvl else f"{n}: +{v} (har lämnat guilden)" for n, v in denna.most_common(10))

    ut += ["", f"## Nådde level {MAX_LEVEL}"]
    ut += lista(f"{e['n']}, {tid(e['t'])}" for e in period if e["k"] == "level" and e["v"] >= MAX_LEVEL)

    ut += ["", "## Först i guilden till en ny level"]
    ut += lista(f"Level {L}: {e['n']}, {tid(e['t'])}" for L, e in forst.items() if e["t"] >= fran)
    if fil.stem == RELEASE and forst and min(e["t"] for e in forst.values()) >= fran:
        ut.append(f"- (Hämtningen startade först {tid(min(e['t'] for e in events))}: dings före det syns inte här. Klass-achievements som Novice Rogue har Blizzards exakta tid för level 25.)")

    # Epics och kompletta set: guildens första någonsin, och alla nya under perioden
    for kind, rubrik in (("epic", "Epics (första gången någon har en på sig)"), ("set", "Kompletta set")):
        alla = [e for e in events if e["k"] == kind]
        ut += ["", f"## {rubrik}"]
        if alla and alla[0]["t"] >= fran:
            ut.append(f"- Först i guilden: {alla[0]['n']} med {alla[0]['v']}, {tid(alla[0]['t'])}")
        ut += lista(f"{e['n']}: {e['v']}, {tid(e['t'])}" for e in alla if e["t"] >= fran)

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

    # ---------- Spelstatistiken (Forever): veckans titlar, guildens summor ----------
    # Statistiken räknas från karaktärens start. Började mätningen inom perioden är totalen veckans siffra,
    # annars skillnaden mot dagssnapshoten när perioden började (ungefärlig: snapshoten är dagens sista läge).
    har_stat = [m for m in members if m.get("stat") is not None]
    if har_stat:
        total = fil.stem > tid(fran)[:10] or not any((v or {}).get("stat") for v in start.values())

        def vecka(m, rader):
            nu_ = sum((m["stat"] or {}).get(r, 0) for r in rader)
            if total:
                return nu_
            gammal = (start.get(m["name"]) or {}).get("stat")
            return nu_ - sum(gammal.get(r, 0) for r in rader) if gammal is not None else None

        ut += ["", "## Veckans titlar (ur spelstatistiken, topp 3)"]
        ut.append("Räknat från karaktärernas start, alltså sedan releasen." if total else "Ökningen under perioden.")
        for titel, vad, rader in TITLAR:
            topp = sorted(((m["name"], vecka(m, rader)) for m in har_stat), key=lambda x: -(x[1] or 0))
            topp = [(n, v) for n, v in topp if v][:3]
            ut.append(f"- {titel} ({vad}): " + (", ".join(f"{n} {v}" for n, v in topp) if topp else "ingen än"))
        kills = "Total kills that grant experience or honor"
        lugna = sorted(((m["name"], vecka(m, [kills])) for m in har_stat if m["level"] >= 10 and (m.get("lastLogin") or 0) >= fran),
                       key=lambda x: x[1] if x[1] is not None else 10 ** 9)
        ut.append("- Pacifisten (färst kills som ger XP, bland dem på level 10+ som spelat i veckan): "
                  + (", ".join(f"{n} {v}" for n, v in lugna[:3] if v is not None) or "ingen än"))
        ut += ["", "### Guilden tillsammans"]
        summa = {t: sum(vecka(m, r) or 0 for m in har_stat) for t, _, r in TITLAR}
        ut += lista([f"Kills som ger XP: {summa['Massmördaren']}", f"Dödsfall: {summa['Hoggers bästa vän']}",
                     f"Fångade fiskar: {summa['Fiskekungen']}", f"Klarade quests: {summa['Questmaskinen']}",
                     f"Camps: {summa['Lägerelden']}"])
        ut.append(f"- (statistik för {len(har_stat)} av {len(members)} karaktärer: övriga har inte loggat in sedan releasen)")

    # ---------- Forevers achievements: först i guilden under perioden, och nya zoner ----------
    defs = json.loads((FOREVER / "achievements.json").read_text(encoding="utf-8")) if (FOREVER / "achievements.json").exists() else {}
    forsta = {}
    for m in members:
        for n, t in (m.get("ach") or {}).items():
            if n not in forsta or t < forsta[n][1]:
                forsta[n] = (m["name"], t)
    veckans = sorted(((n, w, t) for n, (w, t) in forsta.items() if t >= fran), key=lambda x: x[2])
    zon = lambda n: (defs.get(n) or {}).get("sub") in ("Eastern Kingdoms", "Kalimdor")
    ut += ["", "## Först i guilden med en achievement (Blizzards egna)"]
    ut += lista(f"{n}: {w}, {tid(t)}" + (f" ({sv(defs[n]['desc'])})" if n in defs and defs[n].get("desc") else "")
                for n, w, t in veckans if not zon(n))
    ut += ["", "## Nya zoner utforskade (först i guilden)"]
    ut += lista(f"{n.removeprefix('Explore ')}: {w}, {tid(t)}" for n, w, t in veckans if zon(n))
    zoner = [n for n in defs if zon(n)]
    if zoner:
        ut.append(f"- Totalt utforskade: {sum(n in forsta for n in zoner)} av {len(zoner)} zoner")

    # ---------- Yrken: guildens bästa i varje ----------
    yrken = collections.defaultdict(list)
    for m in members:
        for y, (skill, tak) in (m.get("prof") or {}).items():
            yrken[y].append((skill, m["name"]))
    if yrken:
        ut += ["", "## Yrken (guildens bästa, skill av 300)"]
        ut += lista(f"{y}: " + ", ".join(f"{n} {s_}" for s_, n in sorted(v, reverse=True)[:3]) + f" ({len(v)} har yrket)"
                    for y, v in sorted(yrken.items()))

    ut += ["", "## Högst item level"]
    ut += lista(f"{m['name']}: {m['ilvl']}" for m in sorted(members, key=lambda m: -(m.get("ilvl") or 0))[:5] if m.get("ilvl"))

    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "veckan.txt").write_text("\n".join(ut) + "\n", encoding="utf-8")
    print(f"Veckan klar → dist/veckan.txt ({len(period)} händelser)")


if __name__ == "__main__":
    main()
