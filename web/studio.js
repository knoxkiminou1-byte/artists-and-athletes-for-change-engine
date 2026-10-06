let CATALOG = [], current = "all", output = "";
const $ = id => document.getElementById(id);
function esc(s){ return String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function draw(){
  const q = ($("q").value || "").toLowerCase();
  const rows = CATALOG.filter(r => (current==="all" || r.systems.includes(current)) && (r.name+" "+r.capability+" "+r.repo).toLowerCase().includes(q));
  $("grid").innerHTML = rows.map(r => `<article><span class="badge ${r.status==='wired'?'':r.status==='optional-binary'?'bin':'wait'}">${esc(r.status)}</span><h3>${esc(r.name)}</h3><p>${esc(r.capability)}</p><a href="${r.url}">${esc(r.repo)}</a></article>`).join("");
  $("stats").innerHTML = `<div class="stat"><b>${CATALOG.length}</b><span>MIT</span></div><div class="stat"><b>${CATALOG.filter(r=>r.status==='wired').length}</b><span>wired</span></div><div class="stat"><b>${rows.length}</b><span>showing</span></div>`;
}
function setOut(text){ output = text; $("out").textContent = text; }
async function load(){
  const base = "https://raw.githubusercontent.com/knoxkiminou1-byte/artists-and-athletes-for-change-engine/main/aafc_engine/integrations/";
  const files = ["catalog-a.json", "catalog-b.json"];
  const parts = await Promise.all(files.map(async name => {
    const local = await fetch(name).then(r => r.ok ? r.json() : null).catch(() => null);
    if (local) return local;
    const remote = await fetch(base + name);
    if (!remote.ok) throw new Error(name);
    return remote.json();
  }));
  CATALOG = parts.flat();
  const systems = ["all", ...new Set(CATALOG.flatMap(r => r.systems))];
  $("systems").innerHTML = systems.map(s => `<button class="sys ${s==='all'?'on':''}" data-s="${s}">${s}</button>`).join("");
  $("systems").onclick = e => { if(!e.target.dataset.s) return; current=e.target.dataset.s; [...$("systems").children].forEach(b => b.classList.toggle("on", b.dataset.s===current)); draw(); };
  setOut("Catalog loaded. " + CATALOG.length + " MIT integrations. Run an adapter or filter the list.");
  draw();
}
document.getElementById("q").oninput = draw;
document.getElementById("report").onclick = () => setOut(`# AAFC findings \u2014 ${$("client").value}\n\nEvidence only. Nothing here was inferred.\n\n## Homepage finding\n- Evidence: ${$("finding").value}\n- Why it matters: It blocks the next sale.\n- Fix: Fix the evidenced item only.\n`);
document.getElementById("ledger").onclick = () => setOut("date,kind,amount,status,evidence,project\n2026-10-06,retainer,1500,OWED,signed proposal,sample\n");
document.getElementById("cal").onclick = () => setOut(`BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//AAFC//Studio//EN\nBEGIN:VEVENT\nSUMMARY:Retainer review \u2014 ${$("client").value}\nRRULE:FREQ=MONTHLY;COUNT=3\nEND:VEVENT\nEND:VCALENDAR\n`);
document.getElementById("mail").onclick = () => setOut(`DRY RUN \u2014 not sent\nTo: ${$("email").value}\nSubject: Audit ready\n\n${$("finding").value}\n`);
document.getElementById("save").onclick = () => { const blob = new Blob([output || "No output yet.\n"], {type:"text/plain"}); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "aafc-studio-output.txt"; a.click(); };
load().catch(() => setOut("Catalog did not load."));
