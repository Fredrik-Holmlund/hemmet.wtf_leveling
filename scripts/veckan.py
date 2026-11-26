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
CLASS_ACH = {25: "Novice", 45: "Experienced", 60: "Master"}   # klass-achievements med Blizzards exakta tid för dingen
FOREVER = ROOT / "data" / "forever"
# Veckans titlar ur spelstatistiken: (titel, vad som räknas, statistikrader som summeras). Samma som på Bedrifter
TITLAR = [
    ("Massmördaren", "kills som ger XP", ["Total kills that grant experience or honor"]),
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

    # ---------- Guildens rekord genom tiderna (samma som på Bedrifter), med "NYTT" när rekordet sattes i veckan ----------
    rel = int(datetime.datetime.fromisoformat(RELEASE).replace(tzinfo=TZ).timestamp() * 1000)
    dag_ = lambda t: datetime.datetime.fromtimestamp(t / 1000, TZ).date()
    dings = collections.defaultdict(list)
    for e in events:
        if e["k"] == "level" and e["n"] in lvl:
            dings[e["n"]].append(e)
    cls = {m["name"]: m["cls"] for m in members}
    rel_fil = src / "snapshots" / f"{RELEASE}.json"
    rel_snap = json.loads(rel_fil.read_text(encoding="utf-8")) if rel_fil.exists() else {}
    ach = {m["name"]: m.get("ach") or {} for m in members}

    def ding_at(n, L):
        t = next((e["t"] for e in dings[n] if e["v"] == L), None)
        return t or (ach[n].get(f"{CLASS_ACH[L]} {cls[n].capitalize()}") if L in CLASS_ACH else None)

    def dagar(n):
        """Levels per dag. Releasedagen: från level 1 vid midnatt (hämtningen började först på morgonen)."""
        """Den som kom med i guilden senare räknas inte dagen hen kom med (då vet vi inte varifrån hen levlade)."""
        per, forra_ = collections.Counter(), 1
        if not dings[n]:
            return per
        forsta_dag = dag_(dings[n][0]["t"])
        sen = forsta_dag > dag_(rel)
        for e in dings[n]:
            if not (sen and dag_(e["t"]) == forsta_dag):
                per[dag_(e["t"])] += e["v"] - forra_
            forra_ = e["v"]
        if n in rel_snap:   # releasedagen: dagens sista läge, eftersom dings från natten saknas
            per[dag_(rel)] = max(per[dag_(rel)], (rel_snap[n].get("level") or 1) - 1)
        return per

    def streak(n):
        d = sorted(k for k, v in dagar(n).items() if v > 0)
        best = run = 0
        for i, k in enumerate(d):
            run = run + 1 if i and (k - d[i - 1]).days == 1 else 1
            best = max(best, run)
        return best

    def fart(a, b):
        def v(n):
            x = rel if a == 1 else ding_at(n, a)
            y = ding_at(n, b)
            return (y - x, y) if x and y and y > x else None
        return v

    def lang(ms):
        d_, h_ = divmod(ms // 3_600_000, 24)
        return f"{d_} d {h_} h" if d_ else f"{h_} h {ms % 3_600_000 // 60_000} min"

    def maraton(n):
        per = dagar(n)
        return max(((v, d_) for d_, v in per.items()), default=None)

    def timmar(a, b):
        return lambda n: (sum(a <= datetime.datetime.fromtimestamp(e["t"] / 1000, TZ).hour < b for e in dings[n]), None)

    REKORD = [
        ("Maratondagen", "flest levels på en dag", maraton, lambda v: f"+{v[0]} ({v[1].isoformat()})", False),
        ("Längsta streaken", "dagar i rad med minst en ding", lambda n: (streak(n), None), lambda v: f"{v[0]} d", False),
        ("Hela vägen", f"från releasen till level {MAX_LEVEL}", fart(1, MAX_LEVEL), lambda v: lang(v[0]), True),
        ("Blixten", "från releasen till level 25", fart(1, 25), lambda v: lang(v[0]), True),
        ("Raketen", "från level 25 till 45", fart(25, 45), lambda v: lang(v[0]), True),
        ("Slutspurten", f"från level 45 till {MAX_LEVEL}", fart(45, MAX_LEVEL), lambda v: lang(v[0]), True),
        ("Nattugglan", "dings mellan 00 och 05, totalt", timmar(0, 5), lambda v: str(v[0]), False),
        ("Morgonpigg", "dings mellan 05 och 09, totalt", timmar(5, 9), lambda v: str(v[0]), False),
    ]
    ut += ["", "## Guildens rekord genom tiderna (samma som på Bedrifter, topp 3)"]
    ut.append("NYTT = rekordet sattes under perioden. Fartrekorden räknas från releasen för alla.")
    for titel, vad, f, fmt, lagst in REKORD:
        rad = [(n, v) for n in lvl if (v := f(n)) and v[0] and v[0] > 0]
        rad.sort(key=lambda x: x[1][0] if lagst else -x[1][0])
        def visa(n, v):
            nar = v[1] if isinstance(v[1], (int, type(None))) else int(datetime.datetime.combine(v[1], datetime.time(23, 59), TZ).timestamp() * 1000)
            return f"{n} {fmt(v)}" + (" NYTT" if nar and nar >= fran else "")
        ut.append(f"- {titel} ({vad}): " + (", ".join(visa(n, v) for n, v in rad[:3]) if rad else "ingen än"))

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
        ut.append("Needy och Greedy saknas: Blizzards API visar inte need- och greed-rolls sedan 17 november (oklart om spelet fortfarande räknar dem). På Bedrifter står de kvar som de var då.")
        for titel, vad, rader in TITLAR:
            topp = sorted(((m["name"], vecka(m, rader)) for m in har_stat), key=lambda x: -(x[1] or 0))
            topp = [(n, v) for n, v in topp if v][:3]
            ut.append(f"- {titel} ({vad}): " + (", ".join(f"{n} {v}" for n, v in topp) if topp else "ingen än"))
        kills = "Total kills that grant experience or honor"
        lugna = sorted(((m["name"], vecka(m, [kills])) for m in har_stat if 10 <= m["level"] < MAX_LEVEL and denna.get(m["name"])
                        and kills in (m["stat"] or {})   # saknas raden blir det 0 kills på låtsas
                        # och dingen ska synas i profilen (där statistiken kommer ifrån) jämfört med snapshoten (dagens sista läge)
                        and (total or (m.get("plevel") or 0) > ((start.get(m["name"]) or {}).get("level") or 0))),
                       key=lambda x: x[1] if x[1] is not None else 10 ** 9)
        ut.append("- Pacifisten (färst kills som ger XP, bland dem på level 10–59 som dingat i veckan; på 60 ger inga kills XP): "
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
