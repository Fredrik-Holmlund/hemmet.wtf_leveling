# HEMMET – levelingresan (för AI-assistenter)

Guildsida för WoW Forever med data från Blizzards API. Ska ligga på https://resan.hemmet.wtf.
`README.md` är den fullständiga beskrivningen (arkitektur, datan, formspråket, DEMO, publicering): läs den
först och läs avsnittet Formspråket före alla designändringar. Den här filen tar bara det som README inte säger.

## Hur vi jobbar

- Svenska, i kod, commits och samtal. Koden är kortfattad och matchar omgivningen.
- Ge en tydlig rekommendation, inte en lista med alternativ.
- Vid smakfrågor: bygg en jämförelse eller genomför och var beredd att backa. Spara en kopia av mallen eller app.js före större designbyten.
- Kontrollera alltid resultatet i webbläsaren efter ombyggnad (`python scripts/serve.py`, port 5173).
- Texterna på sidan pratar med guilden. Blått = gör, guld = uppnår, inget grönt, pergament bara för utmärkelser.
- Lägg inte in exempeldata på den riktiga sidan. Regeln gäller inte `DEMO/`.

## Repon

| Repo | Vad | Adress |
|---|---|---|
| `hemmet.wtf_leveling` (det här) | levelingsidan, hämtning, API-vakt | resan.hemmet.wtf |
| `hemmet_prerelease` | rekrytering och `/raiding`, publiceras med `scripts/publicera_prerelease.py` | hemmet.wtf |
| `hemmet.wtf` | kommande huvudsajt, tar över domänen när den är klar | |
| `Hemmet_test` | det gamla repot, stängs av när det här har gått stabilt | |

## Viktigt att veta

- **Boten committar till `main` vid varje körning.** Kör `git pull` innan du ändrar något.
- **Hemligheter:** `.env` lokalt och Secrets i GitHub. Får aldrig committas eller klistras in i en chatt.
- **HEMMET hämtas sedan 2026-11-05** (`data/hemmet`, standard i `hamta.yml`). Testguilden Frienship ligger kvar i `data/hc` men uppdateras inte. Repots Variables (`REALM`, `GUILD`, `OUT`, `NS`) går före standarden, t.ex. för att köra Frienship igen.
- **Forever-API:t** var inte helt öppet 2026-11-04. `static-forever` öppnade natten mot 4 november (föremål, ikoner, raser, achievements), men `dynamic-forever-eu` och `-us` visar bara Blizzards testrealmer (CAMWOW …) och guilder och karaktärer ger 404. Namnrymden heter alltså `forever`, men Blizzard har inte sagt det officiellt. API-vakten (schemat avstängt sedan HEMMET hämtas, kan köras för hand) skapade ett issue när svar eller realmlistor ändrades, men inga nya medan ett är öppet. Spara läget med `--spara-bas` innan ett issue stängs, annars larmar den igen.
- **Blizzards svar:** 403 = namnrymden finns inte, 404 = namnrymden finns men resursen saknas. `get()` i `fetch_hemmet.py` kastar fel på 403.
- **Forever har inga vanliga realmer**, bara typer (PvP, PvE, RP-PvP, RP-PvE). Kontots karaktärslista (`/profile/user/wow?namespace=profile-forever-eu`, kräver inloggning) fungerade natten mot 5 november och visar hur API:t ser ut:
  karaktärerna har `surname` och ingen `realm`, adressen är `/profile/wow/character/<förnamn>-<efternamn>` (t.ex. `bonk-donkus`) utan realm, och den dolda realmen syns bara i `protected-character/6946-<id>` (6946 i EU, där HEMMET spelar PvP).
  Karaktärerna öppnade kl. 02:46 den 5 november (profil, achievements, yrken, quests, reputations; inte character-media). Karaktären länkar till guilden som `/data/wow/guild/hemmet`, och rostern öppnade 04:34 (77 medlemmar). character-media gav fortfarande 404, så porträtten saknas.
  `fetch_hemmet.py` klarar Forever: med `NS=forever` (eller när `forever` hittas automatiskt) används adresser utan realm, och namnet är för- och efternamn (`full_name`), eftersom samma förnamn finns många gånger. För HEMMET: `GUILD=HEMMET`, `NS=forever`, `OUT=data/hemmet` (`REALM` används inte).
- **cron-job.org startar hämtningen** var 30:e minut via GitHubs API, med en token som bara får starta Actions i det här repot och som har ett utgångsdatum. Stannar körningarna: kolla först om token gått ut. GitHubs eget schema är för opålitligt och används bara av API-vakten.
- **Bedrifter** (`resan.hemmet.wtf/bedrifter/`) är samma sida som resan med `data-page="bedrifter"` och `<base href="../">`, byggd av `build_hemmet.py`. Den visar titlar ur spelstatistiken (`stat`), Forevers achievements med Blizzards datum (`ach`), Turisterna och yrkena (`prof`).
  Achievement-listan och ikonerna hämtas för hand med `scripts/ach_static.py` till `data/forever/` (ändras bara med en patch).
  Turisternas karta kommer från spelet via wow.export: `assets/raw/worldmap/` (kontinenternas 12 bitar, zonernas `*highlight.png`, `UiMap.csv` och `UiMapAssignment.csv`). Markeringsbilden täcker zonkartans ruta i bredd men bara 668/1002 av höjden. Riverglades finns inte på kontinentkartan och visas bara bland rutorna. Flaggan är spelets `guildflagtest`-modell med HEMMET:s logga (`assets/raw/world/guildflag/`).
- **Veckobrevet** skrivs här i chatten varje vecka och skickas av användaren i Discord. Underlaget är `dist/veckan.txt` (`python scripts/veckan.py --src data/hemmet`, publiceras också på resan.hemmet.wtf/veckan.txt).
  Skickade brev sparas i `data/hemmet/veckobrev/<datum>.md`, i den version som faktiskt skickades. Nästa brev börjar med en recap och jämför mot förra.
  **Taggar:** `python scripts/taggar.py` skriver `data/hemmet/veckobrev/taggar.local.txt` (ignoreras av git) med `Namn <@discord-id>` för dem i veckan.txt som har kört `/verify`. Skriv dem som `<@id>` i brevet, så blir de riktiga omnämnanden. Det kräver `VECKOBREV_NYCKEL` i `.env` (nyckeln i raiding-databasens Vault, se `veckobrev_taggar` i hemmet.wtf_raiding). Discord-id:n får aldrig hamna i repot eller på sidan.
- **Re-run i Actions kör den gamla committen.** Använd "Run workflow" för att testa nyare kod.
- **Porträtt, ikoner och helkroppsbilder** ligger i Actions-cachen, inte i repot. Utan cache kan en körning ta över 30 minuter. Bilderna sparas i cachen även om körningen stoppas, så nästa fortsätter där den slutade.
