"""
Taggar till veckobrevet: vilka i veckan.txt som har kört /verify på Discord, och deras Discord-omnämnande.

  python scripts/taggar.py            (efter python scripts/veckan.py --src data/hemmet)

Hämtar namn → Discord-id från raiding-databasen (funktionen veckobrev_taggar i hemmet.wtf_raiding) med nyckeln
VECKOBREV_NYCKEL i .env. Körs bara lokalt när brevet skrivs, aldrig i Actions: Discord-id:n ska inte hamna på
den publika sidan. Skriver data/hemmet/veckobrev/taggar.local.txt (ignoreras av git), med en rad per namn som
står i veckan.txt: "Namn <@id>". I brevet skrivs namnet då som <@id>, så blir det ett riktigt omnämnande i Discord.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Raidingsidans Supabase-adress och publika nyckel (samma som i hemmet.wtf_raiding/config.js, gjorda för att vara publika)
SUPABASE_URL = "https://dlpzoncjgsegjjkumomo.supabase.co"
SUPABASE_KEY = "sb_publishable_BdIzPi--BqPDexiVqF4BSw_wdxA7wXN"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    env = dict(l.split("=", 1) for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.lstrip().startswith("#"))
    nyckel = env.get("VECKOBREV_NYCKEL", "").strip().strip('"')
    if not nyckel:
        sys.exit("VECKOBREV_NYCKEL saknas i .env (se CLAUDE.md under Veckobrevet)")
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/rpc/veckobrev_taggar", data=json.dumps({"nyckel": nyckel}).encode(),
                                 headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        rader = json.load(r)
    if not rader:
        sys.exit("Inga taggar: fel nyckel, eller har ingen kört /verify än")
    tagg = {r["karaktar"].lower(): (r["karaktar"], r["discord_id"]) for r in rader}

    veckan = (ROOT / "dist" / "veckan.txt").read_text(encoding="utf-8")
    med = sorted(v for k, v in tagg.items() if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", veckan, re.IGNORECASE))
    ut = ROOT / "data" / "hemmet" / "veckobrev" / "taggar.local.txt"
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_text("".join(f"{n} <@{i}>\n" for n, i in med), encoding="utf-8")
    print(f"{len(rader)} har kört /verify, {len(med)} av dem står i veckan.txt → {ut.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
