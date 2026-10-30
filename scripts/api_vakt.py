"""
Spanar efter Blizzards API för WoW Forever (bara standardbiblioteket).

  python scripts/api_vakt.py              provar och skriver en rapport
  python scripts/api_vakt.py --spara-bas  sparar dagens realmlistor som jämförelse
  python scripts/api_vakt.py --prov       låtsas att något hittats (för att testa issue och mejl)

Två saker räknas som fynd:
  1. en gissad Forever-namnrymd (classicforever, forever …) svarar något annat än sist
     (403 = okänd, 404 = finns men är tom, 200 = lever), jämfört med data/api-vakt.json
  2. en ny realm har dykt upp i en befintlig namnrymd (classicann, classic1x, classic, retail),
     jämfört med data/api-vakt.json — Forever kan hamna i en av dem

Körs dagligen av .github/workflows/vakt.yml, som skapar ett issue vid fynd.
Kräver BNET_ID och BNET_SECRET (.env lokalt, Secrets i Actions).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_hemmet import token  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BAS = ROOT / "data" / "api-vakt.json"
REGIONER = ["eu", "us"]
KANDIDATER = ["classicforever", "forever", "classic-forever", "classicfv", "classicfr", "wowforever",
              "classic2x", "classicplus", "classic60", "classicf", "fvr", "classic4", "classicprog"]
# "" = retail: Forever bygger på retail-klienten och kan hamna i dess namnrymd (dynamic-eu)
KANDA = ["classicann", "classic1x", "classic", ""]
TYPER = ["dynamic", "static", "profile"]


def namnrymd(ns, region, typ="dynamic"):
    return f"{typ}-{ns}-{region}" if ns else f"{typ}-{region}"


def realmer(tok, ns, region, typ="dynamic"):
    """Realmnamnen i en namnrymd, eller HTTP-koden om den inte svarar."""
    url = f"https://{region}.api.blizzard.com/data/wow/realm/index?namespace={namnrymd(ns, region, typ)}&locale=en_GB"
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
        return sorted(r["name"] for r in json.load(urllib.request.urlopen(req, timeout=30))["realms"])
    except urllib.error.HTTPError as e:
        return e.code


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--spara-bas", action="store_true")
    ap.add_argument("--prov", action="store_true")
    args = ap.parse_args()

    tok = token()
    fynd, logg = [], []

    bas = json.loads(BAS.read_text(encoding="utf-8")) if BAS.exists() else {}
    nu = {}
    # Okända namnrymder ger 403. 404 betyder att namnrymden finns men är tom, 200 att den lever.
    status, kand = {}, bas.get("status", {})
    for region in REGIONER:
        for ns in KANDIDATER:
            for typ in TYPER:
                namn = f"{typ}-{ns}-{region}"
                svar = realmer(tok, ns, region, typ)
                kod = 200 if isinstance(svar, list) else svar
                status[namn] = kod
                logg.append(f"{namn}: {svar if isinstance(svar, int) else f'{len(svar)} realmer'}")
                if kod != kand.get(namn, 403):
                    extra = f" med {len(svar)} realmer: {', '.join(svar)}" if isinstance(svar, list) else ""
                    fynd.append(f"**`{namn}` svarar nu {kod}** (var {kand.get(namn, 403)}){extra}")
    nu["status"] = status

    for region in REGIONER:
        for ns in KANDA:
            svar = realmer(tok, ns, region)
            if isinstance(svar, int):
                logg.append(f"{namnrymd(ns, region)}: {svar} (svarade inte)")
                continue
            nyckel = f"{ns or 'retail'}-{region}"
            nu[nyckel] = svar
            nya = sorted(set(svar) - set(bas.get(nyckel, svar)))
            logg.append(f"{namnrymd(ns, region)}: {len(svar)} realmer" + (f", nya: {', '.join(nya)}" if nya else ""))
            if nya:
                fynd.append(f"**Nya realmer i `{namnrymd(ns, region)}`**: {', '.join(nya)}")

    if args.spara_bas:
        BAS.parent.mkdir(parents=True, exist_ok=True)
        BAS.write_text(json.dumps(nu, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Bas sparad: {BAS.relative_to(ROOT)}")
    if args.prov:
        fynd.append("**Provlarm** (`--prov`): inget riktigt fynd, bara ett test av issue och mejl.")

    print("\n".join(logg))
    rapport = ("Vakten hittade något som kan vara Forever-API:t:\n\n" + "\n".join(f"- {f}" for f in fynd)
               + "\n\n<details><summary>Alla svar</summary>\n\n```\n" + "\n".join(logg) + "\n```\n</details>\n")
    (ROOT / "vakt-rapport.md").write_text(rapport, encoding="utf-8")
    print(f"\n{len(fynd)} fynd")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"fynd={'ja' if fynd else 'nej'}\n")


if __name__ == "__main__":
    main()
