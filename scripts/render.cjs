// Builds the profile README from the wall on rexxall.github.io.
// Each poster becomes its own 2x image so each one links to its own plugin.
// Usage: node scripts/render.cjs [kit-url]   (default: the live site)
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PW || "playwright");

const KIT = process.argv[2] || "https://rexxall.github.io/readme-kit.html";
const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "assets", "wall");
const SITE = "https://rexxall.github.io/";

const fmtDate = iso => new Date(iso + (iso.length === 10 ? "T00:00:00Z" : "")).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const esc = s => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  let kit, releases, fetched;
  for (const scheme of ["light", "dark"]) {
    const page = await browser.newPage({ viewport: { width: 960, height: 1400 }, deviceScaleFactor: 2, colorScheme: scheme });
    await page.goto(KIT + (KIT.includes("?") ? "&" : "?") + "t=" + Date.now(), { waitUntil: "networkidle" });
    await page.waitForFunction(() => window.KIT, null, { timeout: 30000 });
    await page.waitForTimeout(400);
    await page.locator("#label").screenshot({ path: path.join(OUT, `label-${scheme}.png`), omitBackground: true });
    await page.locator("#label-narrow").screenshot({ path: path.join(OUT, `label-narrow-${scheme}.png`), omitBackground: true });
    if (scheme === "light") {
      kit = await page.evaluate(() => window.KIT);
      releases = await page.evaluate(() => window.KIT_RELEASES || []);
      fetched = await page.evaluate(() => window.KIT_FETCHED || null);
      for (const p of kit) {
        await page.locator("#p-" + p.id).screenshot({ path: path.join(OUT, `${p.id}.png`), omitBackground: true });
      }
    }
    await page.close();
  }
  await browser.close();

  const total = kit.reduce((a, p) => a + (p.d || 0), 0);
  const rows = [];
  kit.forEach(p => (rows[p.row] = rows[p.row] || []).push(p));
  const cell = p => {
    const href = p.repo ? `https://github.com/Rexxall/${p.repo}` : SITE + "#" + p.id;
    const count = p.d ? `${p.d.toLocaleString("en-US")} downloads` : "web app";
    const pct = (p.pct * 0.994).toFixed(2);
    return `<a href="${href}"><img src="assets/wall/${p.id}.png" width="${pct}%" alt="${esc(p.name)}: ${esc(p.line)} ${count}."></a>`;
  };
  const lines = [
    `<a href="${SITE}"><picture><source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/wall/label-narrow-dark.png"><source media="(max-width: 600px)" srcset="assets/wall/label-narrow-light.png"><source media="(prefers-color-scheme: dark)" srcset="assets/wall/label-dark.png"><img src="assets/wall/label-light.png" width="100%" alt="Rex. Trained in medicine. Speaks Chinese, Uyghur, English and Japanese. Builds the small, local tools his own notes were missing. ${kit.filter(p => p.d).length} Obsidian plugins, ${total.toLocaleString("en-US")} downloads, 2 browser apps. rexxall.github.io"></picture></a>`,
    "",
    `<p>${rows.map(r => r.map(cell).join("")).join("<br>")}</p>`,
    "",
    "**Recent releases**",
    "",
    ...releases.map(r => `- [${r.name} ${r.tag}](https://github.com/Rexxall/${r.repo}/releases/tag/${encodeURIComponent(r.tag)}) · ${fmtDate(r.date)}`),
    "",
    `<sub>Poster size follows downloads from Obsidian’s public stats file${fetched ? ", read " + fmtDate(fetched.slice(0, 10)) : ""}. A download is any install or update, not a person. More on <a href="${SITE}">rexxall.github.io</a>.</sub>`,
    "",
  ];
  fs.writeFileSync(path.join(ROOT, "README.md"), lines.join("\n"));
  // what the images show; the Action commits only when this changes, so pixel noise never makes a commit
  fs.writeFileSync(path.join(OUT, "kit.json"), JSON.stringify({ kit: kit.map(({ id, row, pct, d }) => ({ id, row, pct, d })), releases }, null, 1) + "\n");
  console.log("posters", kit.length, "total", total);
})().catch(e => { console.error(e); process.exit(1); });
