// Fig1 Atlas — client-side gallery. Loads index.json once and filters in the browser.
const ROLES = {
  "pipeline": ["here is how our method works, step by step", "--role-pipeline"],
  "prior-vs-ours": ["existing approaches do X; we do Y", "--role-prior"],
  "before-after": ["input or baseline output vs. our output", "--role-before"],
  "teaser-result": ["look at this headline result or sample quality", "--role-teaser"],
  "problem-setup": ["here is the task or failure mode we address", "--role-problem"],
  "concept": ["here is the intuition, as a cartoon or geometric picture", "--role-concept"],
  "overview-framework": ["here are the parts of a system or benchmark and how they fit", "--role-overview"],
  "analysis-finding": ["we found this phenomenon", "--role-analysis"],
};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const roleChip = r => r ? `<span class="role"><span class="dot" style="background:var(${ROLES[r]?.[1] || "--muted"})"></span>${esc(r)}</span>` : "";
let INDEX = null;
async function loadIndex() { if (!INDEX) INDEX = await (await fetch("index.json")).json(); return INDEX; }

function card(r) {
  const fig = r.thumb_url
    ? `<img loading="lazy" src="${esc(r.thumb_url)}" alt="Figure 1 of ${esc(r.title)}">`
    : `<div class="textfig"><div class="row">text-only · figure not hosted (license)</div><div class="lay">${esc(r.layout)}</div></div>`;
  return `<a class="card" href="paper.html?id=${encodeURIComponent(r.id)}">${fig}
    <div class="meta"><div class="row">${roleChip(r.role)}${r.tier !== "poster" ? `<span class="tier">${esc(r.tier)}</span>` : ""}<span>${esc(r.venue)}</span></div>
    <div class="t">${esc(r.title)}</div><div class="c">${esc(r.claim)}</div></div></a>`;
}

async function gallery() {
  const data = await loadIndex();
  const facets = { venue: {}, role: {}, tier: {}, style: {} };
  data.forEach(r => { facets.venue[r.venue] = (facets.venue[r.venue]||0)+1; facets.role[r.role] = (facets.role[r.role]||0)+1;
    facets.tier[r.tier] = (facets.tier[r.tier]||0)+1; (r.style||[]).forEach(s => facets.style[s] = (facets.style[s]||0)+1); });
  const rail = document.getElementById("rail");
  const group = (key, title, order) => {
    const ks = order || Object.keys(facets[key]).sort((a,b) => facets[key][b]-facets[key][a]);
    return `<div><h4>${title}</h4>${ks.filter(k => facets[key][k]).map(k => `<label><input type="checkbox" data-f="${key}" value="${esc(k)}">
      ${key === "role" ? `<span class="dot" style="background:var(${ROLES[k][1]})"></span>` : ""}${esc(k)}<span class="n">${facets[key][k]}</span></label>`).join("")}</div>`;
  };
  rail.innerHTML = `<input type="search" id="q" placeholder="Search title, claim, tags" aria-label="Search">
    ${group("role", "Role", Object.keys(ROLES))}${group("venue", "Venue")}${group("tier", "Tier", ["oral","spotlight","poster"])}${group("style", "Style")}
    <div><h4>Images</h4><label><input type="checkbox" id="hosted"> hosted images only</label></div>`;
  const grid = document.getElementById("grid"), status = document.getElementById("status");
  let shown = 60, hits = [];
  const render = () => {
    grid.innerHTML = hits.slice(0, shown).map(card).join("");
    status.textContent = `${hits.length.toLocaleString()} of ${data.length.toLocaleString()} figures`;
    document.getElementById("more").hidden = shown >= hits.length;
  };
  const apply = () => {
    const sel = {}; rail.querySelectorAll("input[data-f]:checked").forEach(i => (sel[i.dataset.f] ||= new Set()).add(i.value));
    const words = document.getElementById("q").value.toLowerCase().split(/\s+/).filter(Boolean);
    const hosted = document.getElementById("hosted").checked;
    hits = data.filter(r => (!sel.venue || sel.venue.has(r.venue)) && (!sel.role || sel.role.has(r.role) || sel.role.has(r.role2))
      && (!sel.tier || sel.tier.has(r.tier)) && (!sel.style || (r.style||[]).some(s => sel.style.has(s))) && (!hosted || r.thumb_url)
      && words.every(w => (r.title + " " + r.claim + " " + (r.tags||[]).join(" ") + " " + r.layout).toLowerCase().includes(w)));
    hits.sort((a, b) => (a.thumb_url ? 0 : 1) - (b.thumb_url ? 0 : 1) || ({oral:0,spotlight:1,poster:2}[a.tier]) - ({oral:0,spotlight:1,poster:2}[b.tier]));
    shown = 60; render();
  };
  rail.addEventListener("input", apply);
  document.getElementById("more").onclick = () => { shown += 60; render(); };
  const pre = new URLSearchParams(location.search).get("role");
  if (pre) rail.querySelectorAll(`input[data-f=role][value="${CSS.escape(pre)}"]`).forEach(i => i.checked = true);
  apply();
}

async function paper() {
  const id = new URLSearchParams(location.search).get("id");
  const el = document.getElementById("paper");
  let m; try { m = await (await fetch(`p/${encodeURIComponent(id)}.json`)).json(); } catch { el.innerHTML = `<p>No paper with id <code>${esc(id)}</code>. <a href="./">Back to the gallery</a>.</p>`; return; }
  document.title = `${m.title} · Fig1 Atlas`;
  const L = m.links || {};
  const link = (k, t) => L[k] ? `<a href="${esc(L[k])}" target="_blank" rel="noopener">${t}</a>` : "";
  el.innerHTML = `<div class="row">${roleChip(m.role)}${m.role2 ? roleChip(m.role2) : ""}<span class="tier">${esc(m.tier)}</span><span>${esc(m.venue)}</span><span>· <code>${esc(m.id)}</code></span></div>
    <h1>${esc(m.title)}</h1><div class="authors">${esc((m.authors||[]).join(", "))}</div>
    ${m.image_url ? `<div class="figbox"><img src="${esc(m.image_url)}" alt="Figure 1"></div>
      <div class="attrib">Figure reproduced from the paper under ${esc(m.img.toUpperCase())} (<a href="${esc(m.license)}" target="_blank" rel="noopener">license</a>). © the authors.${m.img.includes("nc") ? " Non-commercial use only." : ""}</div>`
      : `<div class="figbox" style="background:var(--bg)"><p>The image is not hosted because the paper's arXiv license does not permit redistribution. See Figure 1 on page ${(m.figure_page??0)+1} of the ${link("pdf","PDF")}.</p></div>`}
    <div class="cap"><b>Figure 1.</b> ${esc(m.caption)} <span class="attrib">(caption quoted from the paper)</span></div>
    <div class="claim">${esc(m.claim)}</div>
    <dl class="kv"><dt>Layout</dt><dd>${esc(m.layout)}</dd><dt>Style</dt><dd>${esc((m.style||[]).join(", "))}</dd>
      <dt>Tags</dt><dd>${esc((m.tags||[]).join(", "))}</dd><dt>Links</dt><dd>${[link("arxiv","arXiv"), link("openreview","OpenReview"), link("pdf","PDF"), link("code","Code")].filter(Boolean).join(" · ")}</dd></dl>
    <div class="desc"><h4 style="margin:0 0 4px">Description</h4>${esc(m.description)}</div>
    <details><summary>Abstract</summary><p class="desc">${esc(m.abstract)}</p></details>`;
}

async function roles() {
  const data = await loadIndex();
  const el = document.getElementById("roles");
  el.innerHTML = Object.entries(ROLES).map(([r, [def]]) => {
    const ex = data.filter(x => x.role === r && x.thumb_url).sort((a, b) => (b.conf ?? 0) - (a.conf ?? 0)).slice(0, 6);
    const n = data.filter(x => x.role === r).length;
    return `<section><h2>${roleChip(r)}</h2><p>The figure argues: <i>${esc(def)}</i>. ${n} figures. <a href="./?role=${r}">Browse all</a></p>
      <div class="strip">${ex.map(x => `<a href="paper.html?id=${x.id}"><img loading="lazy" src="${esc(x.thumb_url)}" alt=""><span>${esc(x.title.slice(0, 70))}</span></a>`).join("")}</div></section>`;
  }).join("");
}
