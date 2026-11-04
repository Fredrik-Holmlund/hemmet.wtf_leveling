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
- **Testdata:** hardcore-guilden Frienship på Stitches körs tills HEMMET finns. Repots Variables (`REALM`, `GUILD`, `OUT`, `NS`) styr detta. Utan dem körs Frienship.
- **Sätt inte `GUILD=HEMMET` förrän API:t är öppet**, annars fallerar varje körning.
- **Forever-API:t** var inte helt öppet 2026-11-04. `static-forever` öppnade natten mot 4 november (föremål, ikoner, raser, achievements), men `dynamic-forever-eu` och `-us` visar bara Blizzards testrealmer (CAMWOW …) och guilder och karaktärer ger 404. Namnrymden heter alltså `forever`, men Blizzard har inte sagt det officiellt. API-vakten skapar ett issue när svar eller realmlistor ändras, men inga nya medan ett är öppet. Spara läget med `--spara-bas` innan ett issue stängs, annars larmar den igen.
- **Blizzards svar:** 403 = namnrymden finns inte, 404 = namnrymden finns men resursen saknas. `get()` i `fetch_hemmet.py` kastar fel på 403.
- **Forever har inga vanliga realmer**, bara typer (PvP, PvE, RP-PvP, RP-PvE). Kontots karaktärslista (`/profile/user/wow?namespace=profile-forever-eu`, kräver inloggning) fungerade natten mot 5 november och visar hur API:t ser ut:
  karaktärerna har `surname` och ingen `realm`, adressen är `/profile/wow/character/<förnamn>-<efternamn>` (t.ex. `bonk-donkus`) utan realm, och den dolda realmen syns bara i `protected-character/6946-<id>` (6946 i EU, där HEMMET spelar PvP).
  Själva karaktärerna, realm 6946 och guilden svarade fortfarande 404, och listan visade level 1 trots att karaktären var högre. `fetch_hemmet.py` bygger adresser med realm och måste ändras när det öppnar. Guildens adress är okänd.
- **cron-job.org startar hämtningen** var 30:e minut via GitHubs API, med en token som bara får starta Actions i det här repot och som har ett utgångsdatum. Stannar körningarna: kolla först om token gått ut. GitHubs eget schema är för opålitligt och används bara av API-vakten.
- **Re-run i Actions kör den gamla committen.** Använd "Run workflow" för att testa nyare kod.
- **Porträtt, ikoner och helkroppsbilder** ligger i Actions-cachen, inte i repot. Utan cache kan en körning ta över 30 minuter. Bilderna sparas i cachen även om körningen stoppas, så nästa fortsätter där den slutade.
