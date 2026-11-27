/* HEMMET:s meny, samma på alla sidor. Originalet ligger här i hemmet.wtf. De andra sidorna har en kopia av
   exakt den här filen (samma ursprung, så att sidor med inloggning inte laddar skript från en annan sajt).
   Ändra här och kopiera sedan filen till de andra repona.

   Sidan behöver: en <header> med loggan som första länk och en <nav> (id="siteNav" eller den första), och
   <script src="meny.js"></script> direkt efter headern. Menyn byter ut navens innehåll, låter loggan leda till
   hemmet.wtf och lägger till Meny-knappen för mobilen. */
(() => {
  // sajten → [adress, port lokalt]
  const SAJTER = {
    hem: ["hemmet.wtf", 5177], resan: ["resan.hemmet.wtf", 5173], raiding: ["raiding.hemmet.wtf", 5174],
    yrken: ["yrken.hemmet.wtf", 5181], butik: ["butik.hemmet.wtf", 5176], apply: ["apply.hemmet.wtf", 5178],
  };
  // [text, adress inom sajten, data-nav för sidor som byter vy utan sidladdning]
  const MENY = [
    { namn: "Hem", sajt: "hem", hem: true },
    { namn: "Resan", sajt: "resan", under: [["Levelingresan", "#resan"], ["Achievements", "#bedrifter"], ["Bedrifter", "bedrifter/"],
      ["Statistik", "#statistik"], ["Topplistor", "#topp"], ["Grupp", "#grupp"], ["Jämför", "#jamfor"]] },
    { namn: "Raiding", sajt: "raiding", under: [["Översikt", "#start", "start"], ["Raidgrupper", "#raidgrupper", "raidgrupper"],
      ["Kalender", "#kalender", "kalender"], ["Roller &amp; ansvar", "#roller", "roller"]] },
    { namn: "Professions", sajt: "yrken" },
    { namn: "Butiken", sajt: "butik", under: [["Hyllan", "#/"], ["Frågor", "#faq"]] },
    { namn: "Om oss", sajt: "hem", del: "#faq" },
  ];

  const lokal = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  const har = Object.keys(SAJTER).find(k => lokal ? Number(location.port) === SAJTER[k][1] : location.hostname.replace(/^www\./, "") === SAJTER[k][0]);
  const adr = k => lokal ? `http://localhost:${SAJTER[k][1]}/` : `https://${SAJTER[k][0]}/`;

  const nav = document.getElementById("siteNav") || document.querySelector("header nav");
  if (!nav) return;
  const bar = nav.closest("header") || nav.parentElement;
  bar.classList.add("hm-bar");
  if (getComputedStyle(bar).position === "static") bar.style.position = "relative";   // mobilmenyn hänger under
  const logga = bar.querySelector("a");
  if (logga && !nav.contains(logga)) { logga.href = adr("hem"); logga.setAttribute("aria-label", "HEMMET, till hemmet.wtf"); }
  const pil = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';

  nav.classList.add("hm-nav");
  nav.setAttribute("aria-label", "HEMMET");
  nav.innerHTML = MENY.map(m => {
    const pa = m.sajt === har;   // man är på den här delen: länkarna stannar på sidan
    const till = s => pa ? s : adr(m.sajt) + s;
    if (!m.under) return `<a class="hm-top${m.hem ? " hm-hem" : ""}" href="${pa && m.del ? m.del : adr(m.sajt) + (m.del ?? "")}"${pa && !m.del ? ' aria-current="true"' : ""}>${m.namn}</a>`;
    return `<div class="hm-drop${pa ? " hm-drop--har" : ""}">
      <a class="hm-top" href="${pa ? m.under[0][1] : adr(m.sajt)}"${pa ? ' aria-current="true"' : ""}>${m.namn}${pil}</a>
      <div class="hm-panel"><div class="hm-lista">${m.under.map(([t, h, v]) =>
        `<a href="${till(h)}"${pa && v ? ` data-nav="${v}"` : ""}>${t}</a>`).join("")}</div></div>
    </div>`;
  }).join("");

  // mobil: allt bakom en knapp, med sidorna i den del man är på utfällda under
  const knapp = document.createElement("button");
  knapp.type = "button"; knapp.className = "hm-knapp"; knapp.textContent = "Meny";
  knapp.setAttribute("aria-expanded", "false");
  (nav.parentElement === bar ? bar : nav.parentElement).append(knapp);
  const stang = () => { bar.classList.remove("is-open"); knapp.setAttribute("aria-expanded", "false"); };
  knapp.addEventListener("click", () => knapp.setAttribute("aria-expanded", String(bar.classList.toggle("is-open"))));
  nav.addEventListener("click", e => { if (e.target.closest("a")) stang(); });
  addEventListener("keydown", e => { if (e.key === "Escape") { stang(); document.activeElement?.closest?.(".hm-drop") && document.activeElement.blur(); } });

  const css = document.createElement("style");   // .hm-bar .hm-nav … väger mer än sidornas egna menyregler
  css.textContent = `
.hm-nav { display: flex; align-items: center; gap: 24px; overflow: visible !important; }
.hm-nav a { padding: 6px 0; font: 600 14px/1 var(--font-body, "Open Sans", sans-serif); text-decoration: none; color: var(--text-muted, #a59d8c); white-space: nowrap; }
.hm-nav a:hover, .hm-nav a:focus-visible { color: var(--text-primary, #efe5d2); }
.hm-top { position: relative; display: inline-flex; align-items: center; gap: 6px; }
.hm-top svg { width: 10px; height: 10px; opacity: .65; transition: transform .2s; }
.hm-nav .hm-top[aria-current] { color: var(--text-primary, #efe5d2); }
.hm-top[aria-current]::after { content: ""; position: absolute; left: 0; right: 0; bottom: -4px; height: 2px; border-radius: 2px; background: var(--gold-300, #e2c27c); }
/* Hem först, med ett tunt streck före resten */
.hm-hem { margin-right: 6px; }
.hm-hem::before { content: ""; position: absolute; right: -16px; top: 50%; width: 1px; height: 16px; margin-top: -8px; background: var(--line-strong, rgba(255,255,255,.16)); }
.hm-drop { position: relative; }
.hm-panel { position: absolute; top: 100%; left: -14px; z-index: 40; padding-top: 14px; opacity: 0; visibility: hidden; transform: translateY(-4px);
  transition: opacity .16s, transform .16s, visibility .16s; }
.hm-lista { display: flex; flex-direction: column; min-width: 180px; padding: 6px; border-radius: 6px; border: 1px solid var(--line-strong, rgba(255,255,255,.16));
  background: rgba(8, 12, 22, .97); box-shadow: 0 18px 40px -12px rgba(0, 0, 0, .85); }
.hm-bar .hm-nav .hm-lista a { padding: 10px 12px; border-radius: 4px; text-shadow: none; }
.hm-bar .hm-nav .hm-lista a:hover { background: rgba(255, 255, 255, .05); }
.hm-bar .hm-nav .hm-lista a[aria-current], .hm-bar .hm-nav .hm-lista a[aria-current]:hover { color: var(--gold-300, #e2c27c); }
.hm-drop:hover .hm-panel, .hm-drop:focus-within .hm-panel { opacity: 1; visibility: visible; transform: none; }
.hm-drop:hover .hm-top svg, .hm-drop:focus-within .hm-top svg { transform: rotate(180deg); }
.hm-knapp { display: none; padding: 9px 12px; border-radius: 4px; border: 1px solid var(--line-strong, rgba(255,255,255,.16)); background: rgba(255, 255, 255, .03);
  color: var(--text-primary, #efe5d2); font: 600 13px/1 var(--font-label, "Cinzel", serif); letter-spacing: .12em; text-transform: uppercase; cursor: pointer; flex: none; }
@media (max-width: 900px) {
  .hm-knapp { display: inline-flex; }
  .hm-nav { display: none !important; }
  .hm-bar.is-open .hm-nav { display: flex !important; position: absolute; top: 100%; left: 0; right: 0; flex-direction: column; align-items: stretch; gap: 0;
    max-height: calc(100svh - 70px); overflow-y: auto !important; padding: 4px 16px 14px; background: var(--obsidian-950, #04070f); border-bottom: 1px solid var(--line, rgba(255,255,255,.08)); }
  .hm-bar .hm-nav > a, .hm-bar .hm-drop > .hm-top { display: flex; padding: 14px 0; font-size: 16px; }
  .hm-drop:not(.hm-drop--har) .hm-panel { display: none; }   /* på mobilen: bara sidorna i den del man är på */
  .hm-nav > * + * { border-top: 1px solid var(--line, rgba(255,255,255,.08)); }
  .hm-top svg, .hm-top[aria-current]::after, .hm-hem::before { display: none; }
  .hm-hem { margin-right: 0; }
  .hm-nav .hm-top[aria-current] { color: var(--gold-300, #e2c27c); }
  .hm-panel { position: static; opacity: 1; visibility: visible; transform: none; padding: 0 0 8px; }
  .hm-lista { min-width: 0; padding: 0 0 0 14px; border: 0; border-left: 1px solid var(--line-strong, rgba(255,255,255,.16)); border-radius: 0; background: none; box-shadow: none; }
  .hm-bar .hm-nav .hm-lista a { padding: 9px 0 9px 4px; font-size: 15px; }
  .hm-bar .hm-nav .hm-lista a:hover { background: none; }
}`;
  document.head.append(css);
})();
