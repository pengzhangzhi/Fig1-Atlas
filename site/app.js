// Fig1 Atlas: client-side gallery. Loads index.json once and filters in the browser.
const REPO = "https://github.com/pengzhangzhi/Fig1-Atlas";
const ROLES = {
  "pipeline": { name: "Pipeline", argues: "here is how our method works, step by step",
    look: "boxes and arrows from left to right, stages, data flowing through modules", pick: "propose a method whose novelty is the procedure" },
  "prior-vs-ours": { name: "Prior vs. ours", argues: "existing approaches do X; we do Y",
    look: "side-by-side panels, “(a) prior, (b) ours”, contrasting colors, a cross against a check", pick: "improve on a known approach and need the reader to see the difference at a glance" },
  "before-after": { name: "Before and after", argues: "input or baseline output against our output",
    look: "sample grids, input to output, a baseline row above an ours row", pick: "fix a visible failure such as artifacts, hallucination or a wrong answer" },
  "teaser-result": { name: "Teaser result", argues: "look at this headline result or sample quality",
    look: "one large scatter, bar or Pareto plot with ours highlighted, or a gallery of samples", pick: "have one number or one gallery that sells the paper" },
  "problem-setup": { name: "Problem setup", argues: "here is the task or failure mode we address",
    look: "a worked example of the problem, a dialogue, an annotated failure case", pick: "introduce a new task, threat model or failure mode" },
  "concept": { name: "Concept", argues: "here is the intuition, as a cartoon or geometric picture",
    look: "abstract geometry, distributions, loss landscapes, toy 2-D sketches", pick: "have a theoretical or conceptual core idea" },
  "overview-framework": { name: "Overview", argues: "here are the parts of a system or benchmark and how they fit",
    look: "hub and spoke, a grid of components, taxonomy trees, mosaics of benchmark tasks", pick: "introduce a benchmark, a dataset, a survey or a system with several parts" },
  "analysis-finding": { name: "Analysis finding", argues: "we found this phenomenon",
    look: "plots of an empirical trend, scaling curves, attention maps that show a surprise", pick: "are empirical, with an observation as the contribution" },
};
const PROMPT = `I'm writing a paper and need a Figure 1.
My draft: {{path to your draft, or paste it here}}

Use Fig1 Atlas to design it: clone ${REPO} and follow its SKILL.md.
Show me 3 to 5 Figure 1s from accepted papers that make the same kind of argument as mine, recommend one, and sketch how my content fills its layout. After I pick, draft the figure.`;

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = n => Number(n).toLocaleString("en-US");
const roleName = r => ROLES[r]?.name || r || "";
const venueLine = r => r.tier && r.tier !== "poster" ? `${r.venue}, ${r.tier}` : r.venue;
const TIER = { oral: 0, spotlight: 1, poster: 2 };
const hash = s => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };
const node = html => { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; };

let INDEX = null;
async function loadIndex() { if (!INDEX) INDEX = await (await fetch("index.json")).json(); return INDEX; }

function chrome(active) {
  const nav = [["figures", "./", "Figures"], ["roles", "roles.html", "Roles"], ["example", "example.html", "Example run"], ["use", "use.html", "Use it with an agent"]];
  const FAM = [["Fig1 Atlas", "./", "Figure 1s"], ["StoryAtlas", "https://pengzhangzhi.github.io/StoryAtlas/", "how papers frame their work"],
    ["ExperimentAtlas", "https://pengzhangzhi.github.io/ExperimentAtlas/", "how claims are tested"], ["PlotAtlas", "https://pengzhangzhi.github.io/PlotAtlas/", "how results are plotted"]];
  document.getElementById("top").outerHTML = `<header class="top"><div class="brandbox"><a class="brand" href="./">Fig1 Atlas</a>
    <details class="family"><summary aria-label="The Atlas family">Atlas family</summary><ul>${FAM.map(([n, u, d], i) => `<li${i === 0 ? ' class="here"' : ""}><a href="${u}">${n}</a> <span>${d}</span></li>`).join("")}</ul></details></div><nav aria-label="Main">
    ${nav.map(([k, h, t]) => `<a href="${h}"${k === active ? ' aria-current="page"' : ""}>${t}</a>`).join("")}<a href="${REPO}">GitHub</a></nav></header>`;
  document.getElementById("foot").outerHTML = `<footer class="foot"><p>Figures remain © their authors. Images are shown only for papers under an open license (CC BY, CC BY-SA, CC0, CC BY-NC, CC BY-NC-SA); every other paper has a text entry and a link. Roles, claims and descriptions are written by this project and can be wrong.</p>
    <p>Authors: to remove a figure, or to add one, <a href="${REPO}/issues">open an issue</a>. Fig1 Atlas is a non-commercial project.</p></footer>`;
}

// A copyable prompt. {{…}} marks the part the reader replaces.
function promptBox(el, text, label = "Paste into Claude Code or Codex", note = "") {
  const shown = esc(text).replace(/\{\{(.+?)\}\}/g, '<span class="ph">$1</span>');
  const plain = text.replace(/\{\{(.+?)\}\}/g, "<$1>");
  el.innerHTML = `<div class="lbl"><span>${label}</span><button class="btn" type="button">Copy prompt</button></div><pre>${shown}</pre>${note ? `<p class="note">${note}</p>` : ""}`;
  const btn = el.querySelector("button"), pre = el.querySelector("pre");
  btn.onclick = async () => {
    try { await navigator.clipboard.writeText(plain); }
    catch { const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); try { document.execCommand("copy"); } catch {} }
    btn.textContent = "Copied"; btn.classList.add("done");
    setTimeout(() => { btn.textContent = "Copy prompt"; btn.classList.remove("done"); }, 1600);
  };
}

function entry(r, words = []) {
  const hl = s => { let h = esc(s); if (words.length) { const re = new RegExp("(" + words.map(w => esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "gi"); h = h.replace(re, "<mark>$1</mark>"); } return h; };
  const ar = r.ar ? Math.min(Math.max(r.ar, 0.75), 6) : 0;
  const fig = r.thumb_url
    ? `<span class="plate"${ar ? ` style="aspect-ratio:${ar}"` : ""}><img loading="lazy" decoding="async" src="${esc(r.thumb_url)}" alt="Figure 1 of ${esc(r.title)}"></span>`
    : `<span class="plate none">${hl(r.layout)}<small>No image: the paper's license does not allow hosting it. The entry describes the figure and links to the PDF.</small></span>`;
  return `<a class="entry" href="paper.html?id=${encodeURIComponent(r.id)}"${ar ? ` style="--ar:${Math.min(Math.max(r.ar, 1), 3.2)}"` : ""}>${fig}
    <span class="cap"><b>${esc(roleName(r.role))}.</b> ${hl(r.claim)}</span>
    <span class="src"><span class="ti">${hl(r.title)}</span>${esc(venueLine(r))}</span></a>`;
}

// Masonry with a known aspect ratio per image: each entry goes to the shortest column, so order reads across.
function masonry(grid) {
  const GAP = 32, MIN = 330; let cols = [], h = [], n = 0, items = [];
  const build = () => { const k = Math.max(1, Math.floor((grid.clientWidth + GAP) / (MIN + GAP))); if (k === n) return false;
    n = k; grid.textContent = ""; cols = []; h = [];
    for (let i = 0; i < k; i++) { const c = document.createElement("div"); c.className = "col"; grid.append(c); cols.push(c); h.push(0); } return true; };
  const place = ([el, r]) => { const w = (grid.clientWidth - GAP * (n - 1)) / n;
    const est = (r.thumb_url ? w / Math.min(Math.max(r.ar || 2.3, 0.75), 6) : 130) + 160;
    let j = 0; for (let i = 1; i < n; i++) if (h[i] < h[j]) j = i; cols[j].append(el); h[j] += est; };
  new ResizeObserver(() => { if (build()) items.forEach(place); }).observe(grid);
  return { clear() { n = 0; items = []; build(); }, add(pairs) { if (!n) build(); pairs.forEach(p => { items.push(p); place(p); }); } };
}

async function gallery() {
  promptBox(document.getElementById("prompt"), PROMPT, "Paste into Claude Code or Codex", `<a href="example.html">Watch a recorded run, from draft to figure</a>`);
  const grid = document.getElementById("grid"), status = document.getElementById("status"), more = document.getElementById("more"), rail = document.getElementById("rail");
  let data;
  try { data = await loadIndex(); } catch { status.textContent = "The figure index did not load. Reload the page to try again."; return; }
  document.getElementById("count").textContent = num(data.length);
  const count = { role: {}, venue: {}, tier: {}, style: {} };
  for (const r of data) {
    count.role[r.role] = (count.role[r.role] || 0) + 1; count.venue[r.venue] = (count.venue[r.venue] || 0) + 1; count.tier[r.tier] = (count.tier[r.tier] || 0) + 1;
    (r.style || []).forEach(s => count.style[s] = (count.style[s] || 0) + 1);
    r._h = (r.title + " " + r.claim + " " + (r.tags || []).join(" ") + " " + r.layout).toLowerCase(); r._k = hash(r.id);
  }
  const checks = (key, title, keys) => `<h2>${title}</h2>${keys.filter(k => count[key][k]).map(k =>
    `<label class="check"><input type="checkbox" data-f="${key}" value="${esc(k)}">${esc(k[0].toUpperCase() + k.slice(1))}<span class="n">${num(count[key][k])}</span></label>`).join("")}`;
  const byCount = key => Object.keys(count[key]).sort((a, b) => count[key][b] - count[key][a]);
  rail.innerHTML = `<input type="search" id="q" placeholder="Search claims, titles, tags" aria-label="Search claims, titles and tags">
    <h2 class="rolehead">What the figure argues</h2>
    <div class="roles"><button class="rolebtn" type="button" data-role=""><span class="nm">All roles</span><span class="n">${num(data.length)}</span></button>
    ${Object.entries(ROLES).map(([k, v]) => `<button class="rolebtn" type="button" data-role="${k}"><span class="nm">${v.name}</span><span class="n">${num(count.role[k] || 0)}</span><span class="df">${v.argues}</span></button>`).join("")}</div>
    <details id="flt"><summary>Venue, tier and style</summary>
    ${checks("venue", "Venue", byCount("venue").sort())}${checks("tier", "Tier", ["oral", "spotlight", "poster"])}${checks("style", "Style", byCount("style"))}
    <h2>Image</h2><label class="check"><input type="checkbox" id="img">Only entries with an image</label></details>`;
  const flt = document.getElementById("flt"), q = document.getElementById("q"), img = document.getElementById("img");
  if (matchMedia("(min-width: 901px)").matches) flt.open = true;

  // state lives in the URL so a filtered view can be linked
  const P = new URLSearchParams(location.search);
  let role = ROLES[P.get("role")] ? P.get("role") : "";
  q.value = P.get("q") || ""; img.checked = P.get("img") === "1";
  for (const key of ["venue", "tier", "style"]) { const want = new Set((P.get(key) || "").split(",").filter(Boolean));
    rail.querySelectorAll(`input[data-f=${key}]`).forEach(i => i.checked = want.has(i.value)); }

  const m = masonry(grid); let hits = [], shown = 0, words = [];
  const page = () => { const next = hits.slice(shown, shown + 48); shown += next.length;
    m.add(next.map(r => [node(entry(r, words)), r])); more.hidden = shown >= hits.length; };
  const apply = () => {
    const sel = {}; rail.querySelectorAll("input[data-f]:checked").forEach(i => (sel[i.dataset.f] ||= new Set()).add(i.value));
    words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    hits = data.filter(r => (!role || r.role === role) && (!sel.venue || sel.venue.has(r.venue)) && (!sel.tier || sel.tier.has(r.tier))
      && (!sel.style || (r.style || []).some(s => sel.style.has(s))) && (!img.checked || r.thumb_url) && words.every(w => r._h.includes(w)));
    hits.sort((a, b) => (a.thumb_url ? 0 : 1) - (b.thumb_url ? 0 : 1) || TIER[a.tier] - TIER[b.tier] || a._k - b._k);
    rail.querySelectorAll(".rolebtn").forEach(b => b.setAttribute("aria-pressed", b.dataset.role === role));
    const U = new URLSearchParams(); if (role) U.set("role", role); if (q.value.trim()) U.set("q", q.value.trim()); if (img.checked) U.set("img", "1");
    for (const k in sel) U.set(k, [...sel[k]].join(","));
    const qs = U.toString(); history.replaceState(null, "", qs ? "?" + qs : location.pathname);
    const filtered = !!qs, argues = role ? ` that argue “${ROLES[role].argues}”` : "";
    status.innerHTML = hits.length
      ? `${num(hits.length)} ${hits.length === 1 ? "figure" : "figures"}${esc(argues)}${filtered ? `<button type="button" id="clear">Clear filters</button>` : ""}`
      : `No figures match. Try fewer words or another role.<button type="button" id="clear">Clear filters</button>`;
    m.clear(); shown = 0; page();
  };
  let t; q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(apply, 140); });
  rail.addEventListener("change", e => { if (e.target.matches("input[type=checkbox]")) apply(); });
  rail.addEventListener("click", e => { const b = e.target.closest(".rolebtn"); if (b) { role = b.dataset.role; apply(); } });
  status.addEventListener("click", e => { if (e.target.id === "clear") { role = ""; q.value = ""; rail.querySelectorAll("input[type=checkbox]").forEach(i => i.checked = false); apply(); } });
  more.onclick = page;
  apply();
}

async function paper() {
  const id = new URLSearchParams(location.search).get("id") || "", el = document.getElementById("paper");
  let m;
  try { m = await (await fetch(`p/${encodeURIComponent(id)}.json`)).json(); }
  catch { try { m = (await (await fetch("papers.json")).json())[id]; } catch {} }   // bundled preview builds
  if (!m) { el.innerHTML = `<p>There is no figure with the id <code>${esc(id)}</code>. <a href="./">See all figures</a>.</p>`; return; }
  document.title = `${m.title} · Fig1 Atlas`;
  const L = m.links || {}, link = (k, t) => L[k] ? `<li><a href="${esc(L[k])}" target="_blank" rel="noopener">${t}</a></li>` : "";
  const roleLink = r => `<a href="./?role=${r}">${esc(roleName(r))}</a>`;
  const lic = (m.img || "").toUpperCase().replace(/^CC-/, "CC ");
  el.innerHTML = `<a class="back" href="./">All figures</a>
    <h1>${esc(m.title)}</h1>
    <p class="by">${esc((m.authors || []).join(", "))}. ${esc(venueLine(m))}.</p>
    <figure class="figure">${m.image_url
      ? `<div class="plate"><img src="${esc(m.image_url)}" alt="Figure 1 of ${esc(m.title)}"></div>
         <figcaption>Reproduced from the paper under <a href="${esc(m.license)}" target="_blank" rel="noopener">${esc(lic)}</a>. © the authors.${(m.img || "").includes("nc") ? " Non-commercial use only." : ""}</figcaption>`
      : `<div class="plate none">${esc(m.layout)}<small>The image is not hosted here because the paper's license does not allow it. Figure 1 is on page ${(m.figure_page ?? 0) + 1} of the ${L.pdf ? `<a href="${esc(L.pdf)}" target="_blank" rel="noopener">PDF</a>` : "paper"}.</small></div>`}</figure>
    <div class="cols"><div class="read">
      <p class="claim"><b>${esc(roleName(m.role))}.</b> ${esc(m.claim)}</p>
      <h2>Layout</h2><p>${esc(m.layout)}</p>
      <h2>What is drawn</h2><p>${esc(m.description)}</p>
      <h2>The paper's caption</h2><p>Figure 1: ${esc(m.caption)} <span class="quote">Quoted from the paper.</span></p>
      <details><summary>Abstract</summary><p>${esc(m.abstract)}</p></details>
    </div><aside class="facts">
      <h2>Role</h2><ul><li>${roleLink(m.role)}</li>${m.role2 ? `<li>${roleLink(m.role2)}</li>` : ""}</ul>
      <h2>Style</h2><p>${esc((m.style || []).join(", "))}</p>
      <h2>Tags</h2><ul>${(m.tags || []).map(t => `<li><a href="./?q=${encodeURIComponent(t)}">${esc(t)}</a></li>`).join("")}</ul>
      <h2>Paper</h2><ul>${link("arxiv", "arXiv")}${link("openreview", "OpenReview")}${link("pdf", "PDF")}${link("code", "Code")}</ul>
      <h2>Atlas id</h2><p class="id">${esc(m.id)}</p>
    </aside></div>
    <div class="prompt template" id="prompt"></div>
    <section class="related" id="related" hidden></section>`;
  promptBox(document.getElementById("prompt"), `Design Figure 1 for my paper using Fig1 Atlas entry ${m.id} as the layout template.
My draft: {{path to your draft, or paste it here}}

Clone ${REPO}, run python3 scripts/show.py ${m.id} and python3 scripts/fetch_fig.py ${m.id}, then map my content onto that layout panel by panel and draft the figure. Borrow the layout, not the artwork.`, "Use this figure as your template");
  try {
    const data = await loadIndex(), tags = new Set(m.tags || []);
    const rel = data.filter(r => r.id !== m.id && r.thumb_url && r.role === m.role && r.ar >= 1.2 && r.ar <= 3.4).map(r => [r, (r.tags || []).filter(t => tags.has(t)).length])
      .filter(x => x[1] > 0).sort((a, b) => b[1] - a[1] || TIER[a[0].tier] - TIER[b[0].tier]).slice(0, 6).map(x => x[0]);
    if (rel.length >= 3) { const s = document.getElementById("related"); s.hidden = false;
      s.innerHTML = `<h2>Figures that argue the same way, on a related topic</h2><div class="row">${rel.map(r => entry(r)).join("")}</div>`; }
  } catch {}
}

async function roles() {
  const el = document.getElementById("roles");
  let data; try { data = await loadIndex(); } catch { data = []; }
  el.innerHTML = Object.entries(ROLES).map(([k, v]) => {
    const all = data.filter(x => x.role === k);
    const ex = all.filter(x => x.thumb_url && x.ar >= 1.2 && x.ar <= 3.2).sort((a, b) => (b.conf ?? 0) - (a.conf ?? 0) || TIER[a.tier] - TIER[b.tier] || hash(a.id) - hash(b.id)).slice(0, 4);
    return `<section class="role" id="${k}"><h2>${v.name}</h2><p class="argues">The figure argues: ${v.argues}.</p>
      <dl><dt>Typical look</dt><dd>${v.look}</dd><dt>Pick it for papers that</dt><dd>${v.pick}</dd></dl>
      <div class="row">${ex.map(r => entry(r)).join("")}</div>
      ${all.length ? `<p style="margin-top:22px"><a href="./?role=${k}">See all ${num(all.length)} ${v.name.toLowerCase()} figures</a></p>` : ""}</section>`;
  }).join("");
}

// Example page: reveal the recorded steps one at a time.
function replay() {
  const btn = document.getElementById("play"), steps = [...document.querySelectorAll("#tl > li")]; let timer = null;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const stop = () => { clearTimeout(timer); timer = null; steps.forEach(s => s.hidden = false); btn.textContent = "Play step by step"; };
  btn.onclick = () => {
    if (timer) return stop();
    steps.forEach(s => s.hidden = true); btn.textContent = "Show everything"; let i = 0;
    const next = () => { if (i >= steps.length) return stop(); const s = steps[i++]; s.hidden = false;
      s.scrollIntoView({ behavior: calm ? "auto" : "smooth", block: i === 1 ? "center" : "start" });
      timer = setTimeout(next, s.classList.contains("answer") ? 5200 : 2400); };
    next();
  };
}
