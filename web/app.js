/* Stark Travel Desk — dashboard (vanilla JS, no build step). */
(() => {
  "use strict";

  // ------------------------------------------------------------ icons
  const I = {
    plane: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>',
    train: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 11h14M9 21l-2-4M15 21l2-4M8.5 14h.01M15.5 14h.01M12 3v8"/></svg>',
    bus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6v6M15 6v6M2 12h19.6M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"/><circle cx="7" cy="18" r="2"/><path d="M9 18h5"/><circle cx="16" cy="18" r="2"/></svg>',
    cab: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9L18.4 10.6 16 7H8L5.6 10.6 3.5 11.1C2.7 11.3 2 12.1 2 13v3c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg>',
    hotel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/></svg>',
    other: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2M13 17v2M13 11v2"/></svg>',
    cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
    clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    pencil: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>',
    radio: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5M19.1 4.9C23 8.8 23 15.1 19.1 19"/><circle cx="12" cy="12" r="2"/></svg>',
    send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    sync: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>',
  };
  const MODE_COLOR = { flight: "var(--sky)", train: "var(--green)", bus: "var(--amber)", cab: "var(--violet)", hotel: "var(--ink-2)", other: "var(--muted)" };
  const TYPE_LABEL = { flight: "Flight", train: "Train", bus: "Bus", cab: "Cab", hotel: "Hotel Stay", other: "Booking" };
  const STATUSES = [["reserved", "Reserved"], ["confirmed", "Confirmed"], ["waitlisted", "Waitlisted"], ["delayed", "Delayed"], ["completed", "Completed"], ["cancelled", "Cancelled"]];
  const SLABEL = Object.fromEntries(STATUSES);
  const PHASES = [["upcoming", "Upcoming"], ["ongoing", "Ongoing"], ["completed", "Completed"], ["cancelled", "Cancelled"], ["all", "All"]];

  // ------------------------------------------------------------ state
  const S = {
    user: null, view: "trips", trips: [], status: {}, travelers: [], settings: null,
    q: "", phase: "upcoming", mode: "", attention: false, openLogs: {}, logs: {},
    emails: [], wa: [], pending: [], busy: false,
  };

  // ------------------------------------------------------------ utils
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function fmtDate(d) { if (!d) return ""; const [y, m, dd] = d.split("-").map(Number); return `${dd} ${MON[m - 1]} ${y}`; }
  function fmtTime(t) { if (!t) return ""; let [h, m] = t.split(":").map(Number); const ap = h >= 12 ? "PM" : "AM"; h = h % 12 || 12; return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")} ${ap}`; }
  function ago(ts) {
    if (!ts) return "never"; const s = Date.now() / 1000 - ts;
    if (s < 60) return "just now"; if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)} h ago`;
    const d = new Date(ts * 1000); return `${d.getDate()} ${MON[d.getMonth()]}, ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  }
  function waDigits(p) { let d = String(p || "").replace(/\D/g, ""); if (d.length === 10) d = "91" + d; return d; }
  const waLink = (phone, text) => `https://wa.me/${waDigits(phone)}?text=${encodeURIComponent(text || "")}`;
  const TRIG = { new_trip: "Booking confirmation", status: "Status change", reminder: "Departure reminder", manual: "Trip details", test: "Test" };
  const initials = (n) => (n || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]).join("").toUpperCase();
  function toast(msg, bad) {
    const t = $("#toast"); t.innerHTML = `<div class="${bad ? "bad" : ""}">${esc(msg)}</div>`;
    clearTimeout(toast.h); toast.h = setTimeout(() => (t.innerHTML = ""), bad ? 6000 : 3000);
  }
  async function api(path, opts = {}) {
    const res = await fetch("/api" + path, {
      method: opts.method || "GET", credentials: "same-origin",
      headers: opts.body ? { "Content-Type": "application/json" } : {},
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = {}; try { data = await res.json(); } catch { /* empty */ }
    if (res.status === 401 && path !== "/login") { S.user = null; renderLogin(); throw new Error("Please sign in."); }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status}).`);
    return data;
  }
  async function copy(text, input) {
    try { await navigator.clipboard.writeText(text); toast("Copied"); } catch { if (input) { input.focus(); input.select(); } toast("Press Ctrl+C to copy"); }
  }

  // ------------------------------------------------------------ login
  function renderLogin(err) {
    $("#app").innerHTML = `<div class="login"><form id="loginForm">
      <div class="brand"><div class="brand-mark">${I.plane}</div><div><b>Stark Travel Desk</b><small>travel.starkpeople.in</small></div></div>
      <h1>Sign in</h1><p>Admins only. Ask the desk owner for an account.</p>
      <div class="field"><label for="lu">Username</label><input id="lu" autocomplete="username" required></div>
      <div class="field"><label for="lp">Password</label><input id="lp" type="password" autocomplete="current-password" required></div>
      <label class="check"><input type="checkbox" id="lr" checked><span>Keep me signed in for 14 days</span></label>
      <div class="err" id="lerr">${esc(err || "")}</div>
      <button class="btn primary" type="submit">Sign in</button></form></div>`;
    $("#lu").focus();
    $("#loginForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const r = await api("/login", { method: "POST", body: { username: $("#lu").value, password: $("#lp").value, remember: $("#lr").checked } });
        S.user = r.user; boot();
      } catch (ex) { $("#lerr").textContent = ex.message; }
    });
  }

  // ------------------------------------------------------------ shell
  function shell() {
    const st = S.status || {};
    const last = st.gmail_last_sync;
    const chip = !st.gmail_connected ? `<span class="sync-chip"><i></i>Gmail not connected</span>`
      : `<span class="sync-chip ${last && !last.ok ? "bad" : "ok"}" title="${esc(st.gmail_account || "")}"><i></i>${last && !last.ok ? "Gmail sync failed" : "Synced " + ago(last && last.at)}</span>`;
    return `<header class="top"><div class="top-in">
      <div class="brand"><div class="brand-mark">${I.plane}</div><div><b>Stark Travel Desk</b><small>Stark Industries · Corporate travel</small></div></div>
      <nav class="tabs" aria-label="Sections">
        ${[["trips", "Trips"], ["travellers", "Travellers"], ["activity", "Activity"], ["settings", "Settings"]].map(([k, l]) => `<button data-view="${k}" aria-current="${S.view === k ? "page" : "false"}">${l}</button>`).join("")}
      </nav>
      <div class="top-right">${S.pending.length ? `<button class="btn sm wa" data-act="goto-pending">${I.send}${S.pending.length} to send</button>` : ""}${chip}
        <button class="btn sm soft" data-act="sync" ${st.gmail_connected ? "" : "disabled"}>${I.sync}<span>${S.busy ? "Syncing…" : "Sync Gmail"}</span></button>
        <button class="btn sm ghost" data-act="logout" title="Signed in as ${esc(S.user)}">Sign out</button>
      </div></div></header><main id="main"></main>`;
  }
  function render() {
    if (!S.user) return renderLogin();
    $("#app").innerHTML = shell();
    ({ trips: renderTrips, travellers: renderTravellers, activity: renderActivity, settings: renderSettings })[S.view]();
  }

  // ------------------------------------------------------------ trips view
  const today = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  function needsNumber(t) { return t.travelers.some((p) => !p.phone); }
  function filteredTrips() {
    const q = S.q.toLowerCase().split(/\s+/).filter(Boolean);
    return S.trips.filter((t) => {
      if (S.phase !== "all" && t.phase !== S.phase) return false;
      if (S.mode && !t.modes.includes(S.mode)) return false;
      if (S.attention && !(needsNumber(t) || (t.last_whatsapp && t.last_whatsapp.state === "failed") || t.segments.some((s) => s.status === "delayed" || s.status === "waitlisted"))) return false;
      if (!q.length) return true;
      const hay = [t.title, ...t.travelers.map((p) => p.name), ...t.segments.flatMap((s) => [s.origin, s.destination, s.carrier, s.number, s.reference, s.details, s.status_label])].join(" ").toLowerCase();
      return q.every((w) => hay.includes(w));
    }).sort((a, b) => {
      const ka = a.first_date || "9999", kb = b.first_date || "9999";
      return S.phase === "completed" || S.phase === "cancelled" ? (kb > ka ? 1 : kb < ka ? -1 : 0) : (ka > kb ? 1 : ka < kb ? -1 : 0);
    });
  }
  function setupChecklist() {
    const st = S.status || {};
    const hasNumbers = S.trips.length === 0 || S.trips.some((t) => t.travelers.some((p) => p.phone));
    const steps = [
      [st.gmail_connected, "Connect the travel inbox", st.gmail_connected ? `Reading ${esc(st.gmail_account || "Gmail")}` : "Settings → Gmail. Needs a Google OAuth client."],
      [st.decoder_ready, "Add the DeepSeek API key", "Stark Decoder reads tickets and booking emails."],
      [hasNumbers && S.travelers.length > 0, "Save travellers' WhatsApp numbers", "Travellers tab. Names are matched to bookings."],
    ];
    if (steps.every((s) => s[0])) return "";
    return `<section class="setup"><h2>Finish setting up the desk</h2><ol>${steps.map(([ok, b, s]) => `<li class="${ok ? "done" : ""}"><span class="dot">${ok ? I.check : ""}</span><div><b>${b}</b><span>${s}</span></div></li>`).join("")}</ol></section>`;
  }
  function renderTrips() {
    const t0 = today();
    const counts = Object.fromEntries(PHASES.map(([k]) => [k, k === "all" ? S.trips.length : S.trips.filter((t) => t.phase === k).length]));
    const missing = new Set(S.trips.filter((t) => t.phase !== "completed" && t.phase !== "cancelled").flatMap((t) => t.travelers.filter((p) => !p.phone).map((p) => p.name)));
    const departing = S.trips.filter((t) => t.segments.some((s) => s.date === t0 && s.status !== "cancelled")).length;
    const sentToday = (S.status.sent_today ?? null);
    $("#main").innerHTML = `
      ${setupChecklist()}
      ${pendingPanel()}
      <section class="stats">
        <div class="stat"><span class="k">Upcoming trips</span><span class="v">${counts.upcoming}</span><span class="s">${counts.ongoing} travelling now</span></div>
        <div class="stat"><span class="k">Departing today</span><span class="v">${departing}</span><span class="s">Trips with a segment today</span></div>
        <div class="stat ${missing.size ? "warn" : ""}"><span class="k">Missing WhatsApp number</span><span class="v">${missing.size}</span><span class="s">${missing.size ? "Travellers who won't get updates" : "Everyone can be reached"}</span></div>
        <div class="stat ${S.pending.length ? "warn" : ""}"><span class="k">WhatsApp today</span><span class="v">${sentToday ?? "–"}</span><span class="s">${S.pending.length ? `${S.pending.length} waiting to be sent` : "Sent or opened today"}</span></div>
      </section>
      <section class="filters">
        <div class="search">${I.search}<input id="q" type="search" placeholder="Search traveller, city, PNR, train or flight no., hotel…" value="${esc(S.q)}" aria-label="Search trips"></div>
        <div class="seg-ctl" role="group" aria-label="Trip status">${PHASES.map(([k, l]) => `<button data-phase="${k}" aria-pressed="${S.phase === k}">${l} <span class="n">${counts[k]}</span></button>`).join("")}</div>
        <select class="sel" id="mode" aria-label="Mode"><option value="">All modes</option>${["flight", "train", "bus", "cab", "hotel"].map((m) => `<option value="${m}" ${S.mode === m ? "selected" : ""}>${TYPE_LABEL[m]}</option>`).join("")}</select>
        <label class="check" style="align-items:center"><input type="checkbox" id="attn" ${S.attention ? "checked" : ""}><span style="color:var(--ink-2);font-weight:600">Needs attention</span></label>
        <button class="btn" data-act="new-trip">${I.plus}Add trip</button>
      </section>
      <section class="trips" id="tripList"></section>`;
    renderTripList();
  }
  function pendingPanel() {
    if (!S.pending.length) return "";
    return `<section class="panel pending" id="pendingPanel"><div class="panel-h"><div><h2>Needs sending on WhatsApp <span class="count-pill">${S.pending.length}</span></h2>
      <p>Click <b>Open in WhatsApp</b>, then press Send in WhatsApp. The message is already filled in.</p></div></div>
      <ul class="pend-list">${S.pending.map((m) => `<li class="pend" id="pend-${m.id}">
        <span class="avatar">${esc(initials(m.traveler))}</span>
        <div class="grow"><b>${esc(m.traveler)}</b> <span class="mono sub">${esc(m.to_phone)}</span>
          <div class="sub">${esc(TRIG[m.trigger] || m.trigger)} · ${m.trip_id ? `<a href="#" data-act="goto" data-id="${m.trip_id}">${esc(m.title || "Trip")}</a>` : ""} · queued ${ago(m.at)}</div>
          <details><summary>Show message</summary><pre class="msg-pre">${esc(m.body)}</pre></details></div>
        <div class="actions"><a class="btn sm wa-solid" href="${esc(waLink(m.to_phone, m.body))}" target="_blank" rel="noopener" data-act="open-pending" data-mid="${m.id}">${I.send}Open in WhatsApp</a>
          <button class="btn sm ghost" data-act="skip-pending" data-mid="${m.id}">Skip</button></div></li>`).join("")}</ul></section>`;
  }
  function renderTripList() {
    const list = filteredTrips();
    const host = $("#tripList"); if (!host) return;
    if (!S.trips.length) {
      host.innerHTML = `<div class="empty"><h3>No trips yet</h3><p>Trips appear here as soon as booking emails (IRCTC, airlines, Uber, hotels) arrive in the connected Gmail inbox. You can also add one by hand.</p>
        <div class="actions" style="justify-content:center">${S.status.gmail_connected ? `<button class="btn soft" data-act="sync">${I.sync}Sync Gmail now</button>` : `<button class="btn primary" data-view="settings">Connect Gmail</button>`}<button class="btn" data-act="new-trip">${I.plus}Add trip</button></div></div>`;
      return;
    }
    if (!list.length) { host.innerHTML = `<div class="empty"><h3>No trips match</h3><p>Try another status tab, clear the search, or switch off “Needs attention”.</p><button class="btn" data-act="clear-filters">Clear filters</button></div>`; return; }
    host.innerHTML = list.map(tripCard).join("");
  }
  function modeBadge(t) {
    if (t.modes.length === 1) { const m = t.modes[0]; return `<span class="mode-pill"><span style="color:${MODE_COLOR[m]}">${I[m]}</span>${TYPE_LABEL[m]}</span>`; }
    if (!t.modes.length) return `<span class="mode-pill">${I.other}Trip</span>`;
    return `<span class="mode-icons">${t.modes.map((m) => `<span class="mi" style="color:${MODE_COLOR[m]}" title="${TYPE_LABEL[m]}">${I[m]}</span>`).join("")}</span><small>Multi-Mode</small>`;
  }
  function segItem(s) {
    const kind = TYPE_LABEL[s.type] || "Booking";
    const label = s.status_label || SLABEL[s.status] || s.status;
    const whenLbl = s.type === "hotel" ? "Check-In" : "Departs";
    const timeChip = s.start_time ? `<span class="timechip">${I.clock}Time: ${fmtTime(s.start_time)}${s.end_time ? ` → ${fmtTime(s.end_time)}` : ""}</span>` : "";
    const ident = [s.carrier, s.number].filter(Boolean).join(" ");
    const noteBits = [s.details, s.type !== "hotel" && ident && !(s.details || "").includes(s.number || "@@") ? ident : "", s.reference ? `Ref ${s.reference}` : ""].filter(Boolean);
    return `<li class="seg ${s.status === "cancelled" ? "cancelled" : ""}">
      <span class="seg-ic" style="color:${MODE_COLOR[s.type]}">${I[s.type] || I.other}</span>
      <div class="seg-body">
        <div class="seg-top"><span class="seg-kind">${kind}</span><span class="chip st-${esc(s.status)}">${esc(label)}</span></div>
        <div class="seg-route">${esc(s.origin || "—")}<span class="arr">→</span>${esc(s.destination || "—")}</div>
        ${s.date ? `<div class="seg-when">${I.cal}${whenLbl}: <b>${fmtDate(s.date)}</b>${s.end_date && s.end_date !== s.date ? ` <span>→ ${fmtDate(s.end_date)}</span>` : ""}</div>` : `<div class="seg-when">${I.cal}Date not in the email</div>`}
        ${timeChip}
        ${noteBits.length ? `<div class="note">${esc(noteBits.join(" · "))}</div>` : ""}
      </div></li>`;
  }
  function tripCard(t) {
    const phaseLbl = { upcoming: "Upcoming", ongoing: "Ongoing", completed: "Completed", cancelled: "Cancelled" }[t.phase];
    const people = t.travelers.length ? t.travelers.map((p) => `<div class="person"><span class="avatar">${esc(initials(p.name))}</span><div style="min-width:0"><b>${esc(p.name)}</b>${p.phone ? `<small class="mono">${esc(p.phone)}</small>` : `<small class="miss">No WhatsApp number · <button data-act="add-number" data-name="${esc(p.name)}">Add</button></small>`}</div></div>`).join("")
      : `<div class="person"><span class="avatar">?</span><div><b>Not named in the email</b><small><button class="loglink" data-act="edit" data-id="${t.id}" style="color:var(--blue)">Add traveller</button></small></div></div>`;
    const open = S.openLogs[t.id];
    const lw = t.last_whatsapp;
    const waMeta = !lw ? `<div class="wa-meta">No WhatsApp sent yet</div>`
      : `<div class="wa-meta ${lw.state === "failed" ? "bad" : lw.state === "pending" ? "due" : ""}">${{
        sent: "Last WhatsApp sent " + ago(lw.at), opened: "WhatsApp opened " + ago(lw.at), failed: "Last WhatsApp failed " + ago(lw.at),
        pending: "Update waiting to be sent", dismissed: "Last update skipped", skipped: "Last update not sent: " + esc(lw.error || "") }[lw.state] || ""}</div>`;
    return `<article class="trip" id="trip-${t.id}">
      <div class="t-left">
        <div class="t-badges">${modeBadge(t)}<span class="phase ph-${t.phase}">${phaseLbl}</span></div>
        <div class="t-title"><h3>${esc(t.title)}</h3><button class="icon-btn" data-act="edit" data-id="${t.id}" aria-label="Edit trip">${I.pencil}</button></div>
        <div class="t-sec"><span class="lbl">Traveler(s)</span><div class="people">${people}</div></div>
        <div class="t-sec t-log"><div class="row"><span class="lbl">Entry log</span><span class="count">${t.log_count} change${t.log_count === 1 ? "" : "s"}</span></div>
          <button class="loglink" data-act="log" data-id="${t.id}" aria-expanded="${!!open}"><span style="display:inline-grid;width:14px;height:14px">${I.gear}</span>${open ? "Hide log history ▲" : "Load log history ▼"}</button>
          ${open ? `<ul class="loglist">${(S.logs[t.id] || null) === null ? "<li>Loading…</li>" : S.logs[t.id].log.map((l) => `<li class="${l.kind === "whatsapp" ? "wa" : l.kind === "status" ? "st" : ""}">${esc(l.message)}<small>${esc(l.actor)} · ${ago(l.at)}</small></li>`).join("") || "<li>No changes yet.</li>"}</ul>` : ""}
        </div>
      </div>
      <div class="t-mid"><ol class="timeline">${t.segments.length ? t.segments.map(segItem).join("") : `<li class="empty-seg">No segments yet. Use Edit Trip to add the itinerary.</li>`}</ol></div>
      <div class="t-right">
        <button class="btn soft" data-act="track" data-id="${t.id}">${I.radio}Track Live Schedule</button>
        <button class="btn soft" data-act="edit" data-id="${t.id}">${I.pencil}Edit Trip</button>
        <button class="btn wa" data-act="wa" data-id="${t.id}">${I.send}Send to WhatsApp</button>
        ${waMeta}
      </div></article>`;
  }

  // ------------------------------------------------------------ modals
  function modal(html, cls = "") {
    $("#layer").innerHTML = `<div class="modal" data-act="modal-bg"><div class="dialog ${cls}" role="dialog" aria-modal="true">${html}</div></div>`;
    const f = $("#layer input, #layer textarea, #layer select"); if (f) setTimeout(() => f.focus(), 30);
  }
  const closeModal = () => ($("#layer").innerHTML = "");

  // ---- Track live schedule
  function trackLinks(s) {
    const num = (s.number || "").replace(/\s+/g, "");
    if (s.type === "train" && /^\d{5}$/.test(num)) return [["Live running status", `https://www.railyatri.in/live-train-status/${num}`], ["NTES (Indian Railways)", "https://enquiry.indianrail.gov.in/mntes/"]];
    if (s.type === "flight" && num) return [["Flightradar24", `https://www.flightradar24.com/data/flights/${num.toLowerCase()}`], ["Google flight status", `https://www.google.com/search?q=${encodeURIComponent(num + " flight status")}`]];
    if (s.type === "bus" && s.reference) return [["Search booking", `https://www.google.com/search?q=${encodeURIComponent((s.carrier || "") + " " + s.reference + " bus status")}`]];
    return [];
  }
  function openTrack(t) {
    const items = t.segments.map((s) => {
      const links = trackLinks(s);
      return `<div class="track"><span class="seg-ic" style="color:${MODE_COLOR[s.type]}">${I[s.type] || I.other}</span><div class="grow"><b>${esc(s.origin)} → ${esc(s.destination)}</b>
        <small>${esc(TYPE_LABEL[s.type])}${s.number ? " " + esc(s.number) : ""} · ${s.date ? fmtDate(s.date) : "no date"}${s.start_time ? ", " + fmtTime(s.start_time) : ""}</small></div>
        <div class="actions">${links.length ? links.map(([l, u]) => `<a class="btn sm soft" href="${esc(u)}" target="_blank" rel="noopener">${esc(l)}</a>`).join("") : `<small style="color:var(--muted)">${s.type === "hotel" || s.type === "cab" ? "No live tracking for " + (s.type === "hotel" ? "hotels" : "cabs") : "Add the train or flight number to track"}</small>`}</div></div>`;
    }).join("");
    modal(`<div class="dlg-h"><h2>Track live schedule</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div>
      <div class="dlg-b"><p style="margin:0;color:var(--muted)">Opens the live status page for each train and flight in this trip.</p><div class="track-list">${items || "<p>No segments.</p>"}</div></div>`, "narrow");
  }

  // ---- WhatsApp send
  async function openWa(t) {
    modal(`<div class="dlg-h"><h2>Send to WhatsApp</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div><div class="dlg-b"><p>Loading message…</p></div>`, "narrow");
    let p; try { p = await api(`/trips/${t.id}/whatsapp`); } catch (e) { closeModal(); return toast(e.message, true); }
    const ready = S.status.whatsapp_ready;
    if (!ready) return openWaLink(t, p);
    $(".dialog").innerHTML = `<div class="dlg-h"><h2>Send to WhatsApp</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div>
      <form class="dlg-b" id="waForm">
        ${ready ? "" : `<div class="err">WhatsApp sending isn't connected yet. Add the Meta access token and phone number ID in Settings first.</div>`}
        <div class="field"><span class="lab">Send to</span><div class="recips">${(p.travelers.length ? p.travelers : []).map((r, i) => `<label class="recip ${r.phone ? "" : "off"}"><input type="checkbox" name="to" value="${esc(r.name)}" ${r.phone ? "checked" : "disabled"} id="r${i}"><span class="avatar">${esc(initials(r.name))}</span><div class="grow"><b>${esc(r.name)}</b>${r.phone ? `<small class="mono">${esc(r.phone)}</small>` : `<small class="miss">No WhatsApp number saved</small>`}</div>${r.phone ? "" : `<button type="button" class="btn sm" data-act="add-number" data-name="${esc(r.name)}">Add number</button>`}</label>`).join("") || `<p class="err">This trip has no named travellers. Edit the trip to add one.</p>`}</div></div>
        <div class="field"><label for="waBody">Message</label><div class="wa-preview"><textarea id="waBody">${esc(p.body)}</textarea></div><span class="hint">Sent from the Stark Travel Desk WhatsApp Business number.</span></div>
        <div class="err" id="waErr"></div>
      </form>
      <div class="dlg-f"><span></span><div class="r"><button class="btn" data-act="close">Cancel</button><button class="btn wa-solid" id="waSendBtn" ${ready && p.travelers.some((r) => r.phone) ? "" : "disabled"}>${I.send}Send now</button></div></div>`;
    $("#waSendBtn").addEventListener("click", async () => {
      const to = [...document.querySelectorAll('input[name="to"]:checked')].map((x) => x.value);
      if (!to.length) { $("#waErr").textContent = "Pick at least one traveller."; return; }
      $("#waSendBtn").disabled = true; $("#waSendBtn").lastChild.textContent = "Sending…";
      try {
        const r = await api(`/trips/${t.id}/whatsapp`, { method: "POST", body: { body: $("#waBody").value, travelers: to } });
        const sent = r.results.filter((x) => x.state === "sent").length, bad = r.results.filter((x) => x.state !== "sent");
        if (bad.length) { $("#waErr").textContent = bad.map((x) => `${x.traveler}: ${x.error}`).join(" "); $("#waSendBtn").disabled = false; $("#waSendBtn").lastChild.textContent = "Send now"; }
        else { closeModal(); toast(`Sent to ${sent} traveller${sent === 1 ? "" : "s"}`); }
        await refresh(t.id);
      } catch (e) { $("#waErr").textContent = e.message; $("#waSendBtn").disabled = false; $("#waSendBtn").lastChild.textContent = "Send now"; }
    });
  }

  function openWaLink(t, p) {
    const recips = p.travelers;
    $(".dialog").innerHTML = `<div class="dlg-h"><h2>Send to WhatsApp</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div>
      <div class="dlg-b">
        <div class="field"><label for="waBody">Message</label><div class="wa-preview"><textarea id="waBody">${esc(p.body)}</textarea></div>
          <span class="hint">Edit if needed. WhatsApp opens on this device with the message filled in; press Send there.</span></div>
        <div class="field"><span class="lab">Travellers</span><div class="recips">${recips.map((r) => `<div class="recip ${r.phone ? "" : "off"}"><span class="avatar">${esc(initials(r.name))}</span>
          <div class="grow"><b>${esc(r.name)}</b>${r.phone ? `<small class="mono">${esc(r.phone)}</small>` : `<small class="miss">No WhatsApp number saved</small>`}</div>
          ${r.phone ? `<a class="btn sm wa-solid" href="${esc(waLink(r.phone, p.body))}" target="_blank" rel="noopener" data-act="open-manual" data-trip="${t.id}" data-name="${esc(r.name)}" data-phone="${esc(r.phone)}">${I.send}Open in WhatsApp</a>`
            : `<button type="button" class="btn sm" data-act="add-number" data-name="${esc(r.name)}">Add number</button>`}</div>`).join("") || `<p class="err">This trip has no named travellers. Edit the trip to add one.</p>`}</div></div>
      </div>
      <div class="dlg-f"><button class="btn" data-act="copy-wa">Copy message</button><div class="r"><button class="btn" data-act="close">Done</button></div></div>`;
    $("#waBody").addEventListener("input", (e) => {
      document.querySelectorAll('[data-act="open-manual"]').forEach((a) => (a.href = waLink(a.dataset.phone, e.target.value)));
    });
  }

  // ---- Edit trip
  let draft = null;
  function blankSeg() { return { id: null, type: "train", status: "confirmed", status_label: "", origin: "", destination: "", date: "", start_time: "", end_date: "", end_time: "", carrier: "", number: "", reference: "", details: "" }; }
  function openEdit(t) {
    draft = t ? { id: t.id, title: t.title, travelers: t.travelers.map((p) => p.name), cancelled: !!t.cancelled, notes: t.notes || "", segments: t.segments.map((s) => ({ ...s })) }
      : { id: null, title: "", travelers: [], cancelled: false, notes: "", segments: [blankSeg()] };
    drawEdit();
  }
  function drawEdit(errMsg = "") {
    const d = draft;
    const others = S.trips.filter((x) => x.id !== d.id);
    modal(`<div class="dlg-h"><h2>${d.id ? "Edit trip" : "Add trip"}</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div>
    <form class="dlg-b" id="editForm" novalidate>
      <div class="field"><label for="eTitle">Trip title</label><input id="eTitle" value="${esc(d.title)}" placeholder="e.g. Booking Confirmation on IRCTC, Train 16345, LTT - KYJ"></div>
      <div class="field"><span class="lab">Travellers</span><div class="tags" id="eTags">${d.travelers.map((n, i) => `<span>${esc(n)}<button type="button" data-act="rm-trav" data-i="${i}" aria-label="Remove ${esc(n)}">×</button></span>`).join("")}<input id="eTrav" list="travList" placeholder="Type a name and press Enter"></div>
        <datalist id="travList">${S.travelers.map((x) => `<option value="${esc(x.name)}">`).join("")}</datalist>
        <span class="hint">Names are matched to the Travellers directory to find WhatsApp numbers.</span></div>
      <div class="field"><span class="lab">Itinerary</span>
        ${d.segments.map((s, i) => segEditor(s, i)).join("")}
        <div class="actions"><button type="button" class="btn sm" data-act="add-seg">${I.plus}Add segment</button></div></div>
      <div class="field"><label for="eNotes">Notes</label><textarea id="eNotes" rows="2">${esc(d.notes)}</textarea></div>
      ${d.id ? `<label class="check"><input type="checkbox" id="eCancel" ${d.cancelled ? "checked" : ""}><span><b>Trip cancelled</b><span>Moves the trip to Cancelled. Segment statuses stay as they are.</span></span></label>
      <label class="check"><input type="checkbox" id="eNotify" checked><span><b>Send WhatsApp updates for status changes</b><span>Travellers get a message for each segment whose status you change here.</span></span></label>
      ${others.length ? `<div class="field"><label for="eMerge">Merge into another trip</label><div class="copyrow"><select id="eMerge"><option value="">Choose a trip…</option>${others.map((o) => `<option value="${o.id}">${esc(o.title)}${o.first_date ? " · " + fmtDate(o.first_date) : ""}</option>`).join("")}</select><button type="button" class="btn" data-act="merge">Merge</button></div><span class="hint">Moves every segment, traveller and log entry of this trip into the chosen one, then removes this card.</span></div>` : ""}` : ""}
      <div class="err" id="eErr">${esc(errMsg)}</div>
    </form>
    <div class="dlg-f">${d.id ? `<button class="btn danger" data-act="del-trip">Delete trip</button>` : "<span></span>"}<div class="r"><button class="btn" data-act="close">Cancel</button><button class="btn primary" data-act="save-trip">${d.id ? "Save changes" : "Add trip"}</button></div></div>`);
    $("#eTrav").addEventListener("keydown", (e) => {
      if ((e.key === "Enter" || e.key === ",") && e.target.value.trim()) { e.preventDefault(); collectEdit(); draft.travelers.push(e.target.value.trim().replace(/,$/, "")); drawEdit(); $("#eTrav").focus(); }
    });
  }
  function segEditor(s, i) {
    const o = (v) => esc(v || "");
    return `<div class="seg-edit" data-seg="${i}">
      <div class="hd"><b>Segment ${i + 1}</b><div class="actions">${i > 0 ? `<button type="button" class="btn sm ghost" data-act="seg-up" data-i="${i}" aria-label="Move up">↑</button>` : ""}<button type="button" class="btn sm ghost danger" data-act="rm-seg" data-i="${i}">Remove</button></div></div>
      <div class="grid6">
        <div class="field c2"><label>Type</label><select name="type">${Object.keys(TYPE_LABEL).map((k) => `<option value="${k}" ${s.type === k ? "selected" : ""}>${TYPE_LABEL[k]}</option>`).join("")}</select></div>
        <div class="field c2"><label>Status</label><select name="status">${STATUSES.map(([k, l]) => `<option value="${k}" ${s.status === k ? "selected" : ""}>${l}</option>`).join("")}</select></div>
        <div class="field c2"><label>Label shown</label><input name="status_label" value="${o(s.status_label)}" placeholder="CNF, RAC 4…"></div>
        <div class="field c3"><label>${s.type === "hotel" ? "From (e.g. Hotel Stay)" : "From"}</label><input name="origin" value="${o(s.origin)}" placeholder="Mumbai (LTT)"></div>
        <div class="field c3"><label>${s.type === "hotel" ? "Hotel" : "To"}</label><input name="destination" value="${o(s.destination)}" placeholder="Kayamkulam (KYJ)"></div>
        <div class="field c2"><label>${s.type === "hotel" ? "Check-in date" : "Departure date"}</label><input type="date" name="date" value="${o(s.date)}"></div>
        <div class="field c1" style="grid-column:span 1"><label>Time</label><input type="time" name="start_time" value="${o(s.start_time)}"></div>
        <div class="field c2"><label>${s.type === "hotel" ? "Check-out date" : "Arrival date"}</label><input type="date" name="end_date" value="${o(s.end_date)}"></div>
        <div class="field" style="grid-column:span 1"><label>Time</label><input type="time" name="end_time" value="${o(s.end_time)}"></div>
        <div class="field c2"><label>Carrier / hotel chain</label><input name="carrier" value="${o(s.carrier)}" placeholder="IndiGo, Kerala Express"></div>
        <div class="field c2"><label>${s.type === "cab" ? "Vehicle no." : "Flight / train no."}</label><input name="number" value="${o(s.number)}" placeholder="16345"></div>
        <div class="field c2"><label>PNR / booking ref</label><input name="reference" value="${o(s.reference)}"></div>
        <div class="field c6"><label>Details</label><input name="details" value="${o(s.details)}" placeholder="Coach A1, Berth 22, Class 2A AC"></div>
      </div></div>`;
  }
  function collectEdit() {
    if (!$("#editForm")) return;
    draft.title = $("#eTitle").value.trim();
    draft.notes = $("#eNotes").value;
    if ($("#eCancel")) draft.cancelled = $("#eCancel").checked;
    const extra = $("#eTrav").value.trim(); if (extra) { draft.travelers.push(extra); $("#eTrav").value = ""; }
    document.querySelectorAll("[data-seg]").forEach((el) => {
      const s = draft.segments[+el.dataset.seg];
      el.querySelectorAll("[name]").forEach((f) => (s[f.name] = f.value));
    });
  }
  async function saveTrip() {
    collectEdit();
    if (!draft.title) return drawEdit("Give the trip a title.");
    for (const [i, s] of draft.segments.entries()) if (!s.origin && !s.destination) return drawEdit(`Segment ${i + 1} needs a From or To place.`);
    const body = { title: draft.title, travelers: draft.travelers, cancelled: draft.cancelled, notes: draft.notes, segments: draft.segments, notify: $("#eNotify") ? $("#eNotify").checked : false };
    try {
      const r = draft.id ? await api(`/trips/${draft.id}`, { method: "PUT", body }) : await api("/trips", { method: "POST", body });
      closeModal(); toast(draft.id ? "Trip saved" : "Trip added"); await refresh(r.trip.id);
    } catch (e) { $("#eErr").textContent = e.message; }
  }

  // ---- traveller quick add / edit
  function openTraveller(tr, presetName) {
    const t = tr || { name: presetName || "", phone: "", email: "", aliases: "", notify: 1 };
    modal(`<div class="dlg-h"><h2>${tr ? "Edit traveller" : "Add traveller"}</h2><button class="icon-btn" data-act="close" aria-label="Close">${I.x}</button></div>
      <form class="dlg-b" id="trForm">
        <div class="field"><label for="tName">Name as on tickets</label><input id="tName" value="${esc(t.name)}" required></div>
        <div class="field"><label for="tPhone">WhatsApp number</label><input id="tPhone" type="tel" value="${esc(t.phone)}" placeholder="+91 98765 43210"><span class="hint">Include the country code. 10-digit numbers are treated as Indian (+91).</span></div>
        <div class="field"><label for="tEmail">Work email</label><input id="tEmail" type="email" value="${esc(t.email)}" placeholder="name@starkpeople.in"></div>
        <div class="field"><label for="tAliases">Other spellings</label><input id="tAliases" value="${esc(t.aliases)}" placeholder="MR TONY STARK, A STARK"><span class="hint">Comma-separated. Use for how airlines or IRCTC print the name.</span></div>
        <label class="check"><input type="checkbox" id="tNotify" ${t.notify ? "checked" : ""}><span><b>Automatic WhatsApp updates</b><span>Confirmations, status changes and departure reminders.</span></span></label>
        <div class="err" id="tErr"></div>
      </form>
      <div class="dlg-f">${tr ? `<button class="btn danger" data-act="del-trav" data-id="${tr.id}">Delete</button>` : "<span></span>"}<div class="r"><button class="btn" data-act="close">Cancel</button><button class="btn primary" data-act="save-trav" data-id="${tr ? tr.id : ""}">Save traveller</button></div></div>`, "narrow");
  }
  async function saveTraveller(id) {
    const body = { name: $("#tName").value, phone: $("#tPhone").value, email: $("#tEmail").value, aliases: $("#tAliases").value, notify: $("#tNotify").checked };
    try {
      if (id) await api(`/travelers/${id}`, { method: "PUT", body }); else await api("/travelers", { method: "POST", body });
      closeModal(); toast("Traveller saved"); await loadTravellers(); await refresh();
    } catch (e) { $("#tErr").textContent = e.message; }
  }

  // ------------------------------------------------------------ travellers view
  function renderTravellers() {
    const known = new Set(S.travelers.flatMap((t) => [t.name, ...(t.aliases || "").split(",")].map((x) => x.trim().toLowerCase())));
    const unmatched = [...new Set(S.trips.flatMap((t) => t.travelers.filter((p) => !p.traveler_id).map((p) => p.name)))].filter((n) => !known.has(n.toLowerCase()));
    $("#main").innerHTML = `<div class="page-head"><div><h1 class="page">Travellers</h1><p>WhatsApp numbers for everyone who travels. Booking names are matched here.</p></div><button class="btn primary" data-act="new-trav">${I.plus}Add traveller</button></div>
      <section class="panel">
        ${unmatched.length ? `<div class="missing-names"><b>Names on bookings without a number:</b> ${unmatched.map((n) => `<button class="btn sm" data-act="add-number" data-name="${esc(n)}">${I.plus}${esc(n)}</button>`).join("")}</div>` : ""}
        <div class="tbl-wrap"><table class="tbl"><thead><tr><th>Name</th><th>WhatsApp</th><th>Email</th><th>Other spellings</th><th>Auto updates</th><th></th></tr></thead><tbody>
        ${S.travelers.map((t) => `<tr><td><b>${esc(t.name)}</b></td><td class="mono">${esc(t.phone) || '<span class="sub">—</span>'}</td><td>${esc(t.email) || '<span class="sub">—</span>'}</td><td class="sub">${esc(t.aliases)}</td><td>${t.notify ? '<span class="state s-sent">On</span>' : '<span class="state s-skipped">Off</span>'}</td><td><button class="btn sm" data-act="edit-trav" data-id="${t.id}">Edit</button></td></tr>`).join("") || `<tr><td colspan="6" class="sub" style="padding:28px;text-align:center">No travellers yet. Add one so trip updates can reach them on WhatsApp.</td></tr>`}
        </tbody></table></div></section>`;
  }

  // ------------------------------------------------------------ activity view
  async function renderActivity() {
    $("#main").innerHTML = `<div class="page-head"><div><h1 class="page">Activity</h1><p>What the desk read from Gmail and what it sent on WhatsApp.</p></div></div><div id="act">Loading…</div>`;
    try { const [e, w] = await Promise.all([api("/emails"), api("/whatsapp/messages")]); S.emails = e.emails; S.wa = w.messages; } catch (ex) { $("#act").textContent = ex.message; return; }
    const trig = TRIG; const stName = { sent: "Sent", opened: "Opened in WhatsApp", pending: "Waiting", dismissed: "Skipped", skipped: "Not sent", failed: "Failed" };
    $("#act").innerHTML = `<div style="display:grid;gap:16px">
      <section class="panel"><div class="panel-h"><div><h2>WhatsApp messages</h2><p>Latest 150</p></div></div><div class="tbl-wrap"><table class="tbl"><thead><tr><th>When</th><th>Traveller</th><th>Trip</th><th>Why</th><th>Result</th></tr></thead><tbody>
        ${S.wa.map((m) => `<tr><td class="sub">${ago(m.at)}</td><td><b>${esc(m.traveler)}</b><div class="sub mono">${esc(m.to_phone)}</div></td><td>${m.trip_id ? `<a href="#" data-act="goto" data-id="${m.trip_id}">${esc(m.title || "Trip")}</a>` : '<span class="sub">—</span>'}</td><td>${esc(trig[m.trigger] || m.trigger)}</td><td><span class="state s-${m.state}">${stName[m.state] || m.state}</span>${m.error ? `<div class="sub">${esc(m.error)}</div>` : ""}</td></tr>`).join("") || `<tr><td colspan="5" class="sub" style="padding:24px;text-align:center">No messages yet.</td></tr>`}
      </tbody></table></div></section>
      <section class="panel"><div class="panel-h"><div><h2>Emails read by Stark Decoder</h2><p>Booking emails become trips. Other mail is skipped.</p></div>${S.status.gmail_connected ? `<button class="btn sm soft" data-act="sync">${I.sync}Sync now</button>` : ""}</div><div class="tbl-wrap"><table class="tbl"><thead><tr><th>Received</th><th>Email</th><th>Result</th><th></th></tr></thead><tbody>
        ${S.emails.map((m) => `<tr><td class="sub">${ago(m.received_at)}</td><td><b>${esc(m.subject || "(no subject)")}</b><div class="sub">${esc(m.sender)}</div></td><td><span class="state s-${m.state}">${{ parsed: "Trip updated", ignored: "Not a booking", error: "Error" }[m.state]}</span>${m.error ? `<div class="sub">${esc(m.error)}</div>` : ""}${m.trip_id ? `<div><a href="#" data-act="goto" data-id="${m.trip_id}">Open trip</a></div>` : ""}</td><td>${m.state !== "parsed" ? `<button class="btn sm" data-act="retry" data-id="${esc(m.gmail_id)}">Read again</button>` : ""}</td></tr>`).join("") || `<tr><td colspan="4" class="sub" style="padding:24px;text-align:center">No emails read yet.</td></tr>`}
      </tbody></table></div></section></div>`;
  }

  // ------------------------------------------------------------ settings view
  async function renderSettings() {
    $("#main").innerHTML = `<div class="page-head"><div><h1 class="page">Settings</h1><p>Gmail inbox, Stark Decoder, WhatsApp sending and automation.</p></div></div><div id="set">Loading…</div>`;
    try { S.settings = await api("/settings"); } catch (e) { $("#set").textContent = e.message; return; }
    const s = S.settings, st = s.status;
    const secretPh = (k) => (s[k] ? "Saved. Type to replace." : "");
    $("#set").innerHTML = `<form id="setForm" class="settings" novalidate>
      <section class="card-s"><h2>Gmail inbox ${st.gmail_connected ? `<span class="ok-tag">Connected</span>` : `<span class="no-tag">Not connected</span>`}</h2>
        <p>${st.gmail_connected ? `Reading <b>${esc(st.gmail_account)}</b> (read-only). Last sync ${ago(st.gmail_last_sync && st.gmail_last_sync.at)}${st.gmail_last_sync && !st.gmail_last_sync.ok ? ` failed: ${esc(st.gmail_last_sync.error)}` : ""}.` : "Connect the inbox that receives booking emails (IRCTC, airlines, Uber, hotels)."}</p>
        <details class="howto" ${st.gmail_connected ? "" : "open"}><summary>Create the Google OAuth client (one time)</summary><ol>
          <li>Open <a href="https://console.cloud.google.com/apis/library/gmail.googleapis.com" target="_blank" rel="noopener">Google Cloud Console</a>, pick or create a project, and enable the <b>Gmail API</b>.</li>
          <li>OAuth consent screen: User type <b>Internal</b> (Google Workspace) or add the inbox as a test user. Scope: <span class="mono">gmail.readonly</span>.</li>
          <li>Credentials → Create credentials → OAuth client ID → <b>Web application</b>. Authorised redirect URI: the one below.</li>
          <li>Paste the client ID and secret here, save, then press <b>Connect Gmail</b> and sign in as the travel inbox.</li></ol></details>
        <div class="field"><span class="lab">Authorised redirect URI</span><div class="copyrow"><input readonly value="${esc(s.gmail_redirect_uri)}" id="redir"><button type="button" class="btn sm" data-act="copy-redir">Copy</button></div></div>
        <div class="field"><label for="gcid">OAuth client ID</label><input id="gcid" name="gmail_client_id" value="${esc(s.gmail_client_id || "")}" placeholder="…apps.googleusercontent.com"></div>
        <div class="field"><label for="gcs">OAuth client secret</label><input id="gcs" name="gmail_client_secret" type="password" autocomplete="off" placeholder="${secretPh("gmail_client_secret")}"></div>
        <div class="row2"><div class="field"><label for="gmin">Check every (minutes)</label><input id="gmin" name="sync_minutes" type="number" min="5" max="200" value="${esc(s.sync_minutes ?? 10)}"></div>
          <div class="field"><label for="gmax">Emails per check</label><input id="gmax" name="gmail_max" type="number" min="1" max="200" value="${esc(s.gmail_max ?? 40)}"></div></div>
        <div class="field"><label for="gq">Gmail search</label><textarea id="gq" name="gmail_query" rows="3" placeholder="${esc(s.default_gmail_query)}">${esc(s.gmail_query || "")}</textarea><span class="hint">Leave empty for the default, which finds booking, ticket and ride emails from the last 45 days.</span></div>
        <div class="actions"><button type="button" class="btn primary" data-act="gmail-connect">${st.gmail_connected ? "Reconnect Gmail" : "Connect Gmail"}</button>${st.gmail_connected ? `<button type="button" class="btn danger" data-act="gmail-disconnect">Disconnect</button>` : ""}</div>
      </section>
      <section class="card-s"><h2>Stark Decoder ${st.decoder_ready ? `<span class="ok-tag">Ready</span>` : `<span class="no-tag">Needs API key</span>`}</h2>
        <p>DeepSeek reads each booking email and its PDF tickets and turns them into trip segments. Same booking seen again updates the trip; bookings for the same traveller within 3 days are grouped into one trip.</p>
        <div class="field"><label for="ak">DeepSeek API key</label><input id="ak" name="deepseek_api_key" type="password" autocomplete="off" placeholder="${secretPh("deepseek_api_key") || "sk-…"}"><span class="hint">From <a href="https://platform.deepseek.com/api_keys" target="_blank" rel="noopener">platform.deepseek.com</a>. The account needs a positive balance. Stored only on this server.</span></div>
        <div class="field"><label for="dsm">Model</label><input id="dsm" name="deepseek_model" value="${esc(s.deepseek_model || "")}" placeholder="deepseek-chat"><span class="hint">Leave empty for deepseek-chat. PDF tickets are converted to text on this server before they're sent.</span></div>
      </section>
      <section class="card-s"><h2>WhatsApp ${st.whatsapp_ready ? `<span class="ok-tag">Automatic (API)</span>` : `<span class="ok-tag">Click-to-chat</span>`}</h2>
        ${st.whatsapp_ready ? `<p>Messages are sent automatically through the WhatsApp Cloud API. Remove the token below to go back to click-to-chat.</p>`
          : `<p>No setup needed. Updates are queued under <b>Needs sending</b> on the Trips page; an admin clicks <b>Open in WhatsApp</b> and presses Send. Messages go from whichever WhatsApp account is signed in on that phone or computer.</p>`}
        <details class="howto" ${st.whatsapp_ready ? "open" : ""}><summary>Optional: send automatically with the WhatsApp Cloud API</summary>
          <ol>
          <li>In <a href="https://business.facebook.com/settings/system-users" target="_blank" rel="noopener">Meta Business settings → System users</a>, create a system user, assign it your WhatsApp app with full control, and generate a <b>permanent token</b> with <span class="mono">whatsapp_business_messaging</span>.</li>
          <li>In <a href="https://developers.facebook.com/apps/" target="_blank" rel="noopener">your Meta app</a> → WhatsApp → API setup, copy the <b>Phone number ID</b> of the sending number.</li>
          <li>In WhatsApp Manager create a <b>Utility</b> template whose body is just <span class="mono">{{1}}</span> and enter its name below.</li></ol>
          <div style="display:grid;gap:12px;margin-top:12px">
          <div class="field"><label for="wtok">Permanent access token</label><input id="wtok" name="wa_token" type="password" autocomplete="off" placeholder="${secretPh("wa_token") || "EAAG…"}"></div>
          <div class="row2"><div class="field"><label for="wpid">Phone number ID</label><input id="wpid" name="wa_phone_number_id" inputmode="numeric" value="${esc(s.wa_phone_number_id || "")}" placeholder="1098765432109876"></div>
            <div class="field"><label for="wtpl">Template name</label><input id="wtpl" name="wa_template_name" value="${esc(s.wa_template_name || "")}" placeholder="travel_update"></div></div>
          <div class="field"><label for="wlang">Template language code</label><input id="wlang" name="wa_template_lang" value="${esc(s.wa_template_lang || "")}" placeholder="en"></div>
          ${st.whatsapp_ready ? `<div class="field"><label for="wtest">Send a test message to</label><div class="copyrow"><input id="wtest" type="tel" placeholder="+91 98765 43210"><button type="button" class="btn" data-act="wa-test">Send test</button></div></div>
          <div class="actions"><button type="button" class="btn danger sm" data-act="wa-api-off">Switch back to click-to-chat</button></div>` : ""}
          </div></details>
      </section>
      <section class="card-s"><h2>Automatic updates</h2><p>${st.whatsapp_ready ? "What the desk sends on its own." : "What the desk queues under Needs sending on its own."} Travellers without a number, or with updates turned off, are skipped and logged.</p>
        <label class="check"><input type="checkbox" name="auto_new_trip" ${s.auto_new_trip !== false ? "checked" : ""}><span><b>New booking</b><span>Send the itinerary when a booking email becomes a new trip.</span></span></label>
        <label class="check"><input type="checkbox" name="auto_status" ${s.auto_status !== false ? "checked" : ""}><span><b>Status change</b><span>Send when a segment becomes confirmed, delayed, cancelled or completed, from an email or an admin edit.</span></span></label>
        <div class="field"><label for="rh">Departure reminder (hours before)</label><input id="rh" name="reminder_hours" type="number" min="0" max="48" step="0.5" value="${esc(s.reminder_hours ?? 3)}"><span class="hint">0 turns reminders off. Sent once per segment that has a departure or check-in time.</span></div>
      </section>
      <div class="actions" style="grid-column:1/-1"><button type="submit" class="btn primary">Save settings</button><span class="err" id="sErr"></span></div>
    </form>
    <section class="card-s" id="verCard" style="margin-top:16px;max-width:560px"><h2>Site version</h2><p id="verText">Checking…</p></section>
    <form class="card-s" id="pwForm" style="margin-top:16px;max-width:560px"><h2>Your password</h2>
      <div class="row2"><div class="field"><label for="pw1">Current password</label><input id="pw1" type="password" autocomplete="current-password"></div><div class="field"><label for="pw2">New password</label><input id="pw2" type="password" autocomplete="new-password" minlength="10"></div></div>
      <div class="actions"><button class="btn" type="submit">Change password</button><span class="err" id="pwErr"></span></div></form>`;
    showVersion();
  }
  async function showVersion() {
    const el = $("#verText"); if (!el) return;
    try {
      const v = await api("/version");
      el.innerHTML = v.commit
        ? `Running <a class="mono" href="https://github.com/starktvm-hrms/stark-travel-desk/commit/${esc(v.commit)}" target="_blank" rel="noopener">${esc(v.commit.slice(0, 7))}</a>, installed ${ago(v.updated_at)}. New changes on GitHub install automatically every 5 minutes${v.checked_at ? `; last checked ${ago(v.checked_at)}` : ""}.`
        : "Version unknown: this copy isn't a Git checkout, so it won't update itself. Run the setup script on the server.";
    } catch (e) { el.textContent = e.message; }
  }
  async function saveSettings(extra = {}) {
    const f = $("#setForm"); const body = { ...extra };
    f.querySelectorAll("[name]").forEach((el) => { body[el.name] = el.type === "checkbox" ? el.checked : el.value; });
    try { await api("/settings", { method: "PUT", body }); await loadTrips(); toast("Settings saved"); return true; }
    catch (e) { $("#sErr").textContent = e.message; return false; }
  }

  // ------------------------------------------------------------ data
  async function loadTrips() {
    const r = await api("/trips"); S.trips = r.trips; S.status = r.status;
    try {
      const [w, pend] = await Promise.all([api("/whatsapp/messages"), api("/whatsapp/pending")]);
      const d = new Date(); d.setHours(0, 0, 0, 0);
      S.status.sent_today = w.messages.filter((m) => (m.state === "sent" || m.state === "opened") && m.at * 1000 >= d.getTime()).length;
      S.pending = pend.messages;
    } catch { /* ignore */ }
  }
  function updatePendingCount() {
    const c = document.querySelector(".pending .count-pill"); if (c) c.textContent = S.pending.length;
    const b = document.querySelector('[data-act="goto-pending"]'); if (b) b.lastChild.textContent = `${S.pending.length} to send`;
  }
  async function loadTravellers() { S.travelers = (await api("/travelers")).travelers; }
  async function refresh(flashId) {
    await Promise.all([loadTrips(), loadTravellers()]);
    for (const id of Object.keys(S.openLogs)) if (S.openLogs[id]) S.logs[id] = await api(`/trips/${id}/log`).catch(() => ({ log: [] }));
    if (S.view === "trips" && $("#tripList")) { renderTrips(); } else render();
    if (flashId) { const el = $("#trip-" + flashId); if (el) { el.classList.add("flash"); } }
  }
  async function sync() {
    if (S.busy) return; S.busy = true; render();
    try { const r = await api("/gmail/sync", { method: "POST" }); toast(`Checked ${r.checked} new email${r.checked === 1 ? "" : "s"}: ${r.parsed} booking${r.parsed === 1 ? "" : "s"}, ${r.errors} error${r.errors === 1 ? "" : "s"}`, r.errors > 0); }
    catch (e) { toast(e.message, true); }
    S.busy = false; await refresh();
  }

  // ------------------------------------------------------------ events
  document.addEventListener("click", async (e) => {
    const v = e.target.closest("[data-view]");
    if (v) { S.view = v.dataset.view; closeModal(); render(); return; }
    const p = e.target.closest("[data-phase]");
    if (p) { S.phase = p.dataset.phase; renderTrips(); return; }
    const a = e.target.closest("[data-act]");
    if (!a) return;
    const act = a.dataset.act, id = a.dataset.id;
    const trip = id ? S.trips.find((t) => t.id === id) : null;
    if (act === "modal-bg" && e.target !== a) return;
    switch (act) {
      case "modal-bg": case "close": closeModal(); break;
      case "logout": await api("/logout", { method: "POST" }).catch(() => {}); S.user = null; renderLogin(); break;
      case "sync": sync(); break;
      case "clear-filters": S.q = ""; S.mode = ""; S.attention = false; S.phase = "all"; renderTrips(); break;
      case "new-trip": openEdit(null); break;
      case "edit": if (trip) openEdit(trip); break;
      case "track": if (trip) openTrack(trip); break;
      case "wa": if (trip) openWa(trip); break;
      case "log":
        S.openLogs[id] = !S.openLogs[id];
        if (S.openLogs[id]) { S.logs[id] = null; renderTripList(); S.logs[id] = await api(`/trips/${id}/log`).catch(() => ({ log: [] })); }
        renderTripList(); break;
      case "add-number": { const ex = S.travelers.find((t) => t.name.toLowerCase() === (a.dataset.name || "").toLowerCase()); openTraveller(ex || null, a.dataset.name); break; }
      case "new-trav": openTraveller(null); break;
      case "edit-trav": openTraveller(S.travelers.find((t) => t.id === id)); break;
      case "save-trav": saveTraveller(a.dataset.id); break;
      case "del-trav":
        if (a.dataset.confirm) { await api(`/travelers/${id}`, { method: "DELETE" }); closeModal(); toast("Traveller deleted"); await loadTravellers(); refresh(); }
        else { a.dataset.confirm = "1"; a.textContent = "Click again to delete"; }
        break;
      case "rm-trav": collectEdit(); draft.travelers.splice(+a.dataset.i, 1); drawEdit(); break;
      case "add-seg": collectEdit(); draft.segments.push(blankSeg()); drawEdit(); break;
      case "rm-seg": collectEdit(); draft.segments.splice(+a.dataset.i, 1); drawEdit(); break;
      case "seg-up": { collectEdit(); const i = +a.dataset.i; [draft.segments[i - 1], draft.segments[i]] = [draft.segments[i], draft.segments[i - 1]]; drawEdit(); break; }
      case "save-trip": saveTrip(); break;
      case "merge": {
        const into = $("#eMerge").value; if (!into) { $("#eErr").textContent = "Choose the trip to merge into."; break; }
        if (!a.dataset.confirm) { a.dataset.confirm = "1"; a.textContent = "Click again to merge"; break; }
        try { await api(`/trips/${draft.id}/merge`, { method: "POST", body: { into } }); closeModal(); toast("Trips merged"); refresh(into); } catch (ex) { $("#eErr").textContent = ex.message; }
        break;
      }
      case "del-trip":
        if (!a.dataset.confirm) { a.dataset.confirm = "1"; a.textContent = "Click again to delete"; break; }
        await api(`/trips/${draft.id}`, { method: "DELETE" }); closeModal(); toast("Trip deleted"); refresh(); break;
      case "open-pending": {
        // Let the link open WhatsApp, then mark it done here.
        const mid = +a.dataset.mid;
        api("/whatsapp/opened", { method: "POST", body: { id: mid } }).then(() => {
          S.pending = S.pending.filter((m) => m.id !== mid); const li = $("#pend-" + mid); if (li) li.remove();
          if (!S.pending.length) refresh(); else updatePendingCount(); toast("Marked as opened in WhatsApp");
        }).catch((ex) => toast(ex.message, true));
        break;
      }
      case "skip-pending": {
        const mid = +a.dataset.mid;
        try { await api("/whatsapp/dismiss", { method: "POST", body: { id: mid } }); S.pending = S.pending.filter((m) => m.id !== mid); toast("Skipped"); refresh(); } catch (ex) { toast(ex.message, true); }
        break;
      }
      case "goto-pending": S.view = "trips"; render(); setTimeout(() => { const el = $("#pendingPanel"); if (el) el.scrollIntoView({ block: "start" }); }, 30); break;
      case "open-manual":
        api(`/trips/${a.dataset.trip}/whatsapp/opened`, { method: "POST", body: { traveler: a.dataset.name, body: $("#waBody").value } })
          .then(() => { a.textContent = "Opened ✓"; refresh(); }).catch((ex) => toast(ex.message, true));
        break;
      case "copy-wa": copy($("#waBody").value, $("#waBody")); break;
      case "goto": e.preventDefault(); S.view = "trips"; S.phase = "all"; S.q = ""; render(); setTimeout(() => { const el = $("#trip-" + id); if (el) { el.scrollIntoView({ block: "center" }); el.classList.add("flash"); } }, 50); break;
      case "retry":
        a.disabled = true; a.textContent = "Reading…";
        try { const r = await api("/emails/retry", { method: "POST", body: { gmail_id: id } }); toast(r.parsed ? "Trip updated from email" : r.errors ? "Still couldn't read it" : "Not a booking email", !!r.errors); } catch (ex) { toast(ex.message, true); }
        await loadTrips(); renderActivity(); break;
      case "copy-redir": copy($("#redir").value, $("#redir")); break;
      case "gmail-connect": if (await saveSettings()) location.href = "/api/gmail/connect"; break;
      case "gmail-disconnect": if (await saveSettings({ clear_gmail: true })) renderSettings(); break;
      case "wa-api-off":
        if (!a.dataset.confirm) { a.dataset.confirm = "1"; a.textContent = "Click again to remove the token"; break; }
        try { await api("/settings", { method: "PUT", body: { clear_wa_api: true } }); toast("Switched to click-to-chat"); await loadTrips(); renderSettings(); } catch (ex) { toast(ex.message, true); }
        break;
      case "wa-test": {
        const ok = await saveSettings(); if (!ok) break;
        a.disabled = true;
        try { await api("/whatsapp/test", { method: "POST", body: { to: $("#wtest").value } }); toast("Test message sent"); } catch (ex) { toast(ex.message, true); }
        a.disabled = false; break;
      }
    }
  });
  document.addEventListener("input", (e) => {
    if (e.target.id === "q") { S.q = e.target.value; renderTripList(); }
  });
  document.addEventListener("change", (e) => {
    if (e.target.id === "mode") { S.mode = e.target.value; renderTripList(); }
    if (e.target.id === "attn") { S.attention = e.target.checked; renderTripList(); }
  });
  document.addEventListener("submit", async (e) => {
    if (e.target.id === "setForm") { e.preventDefault(); if (await saveSettings()) renderSettings(); }
    if (e.target.id === "trForm") { e.preventDefault(); $('[data-act="save-trav"]').click(); }
    if (e.target.id === "editForm") { e.preventDefault(); }
    if (e.target.id === "pwForm") {
      e.preventDefault();
      try { await api("/password", { method: "POST", body: { current: $("#pw1").value, new: $("#pw2").value } }); toast("Password changed"); $("#pw1").value = $("#pw2").value = ""; $("#pwErr").textContent = ""; }
      catch (ex) { $("#pwErr").textContent = ex.message; }
    }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && $("#layer").innerHTML) closeModal(); });

  // ------------------------------------------------------------ boot
  async function boot() {
    try { S.user = (await api("/me")).user; } catch { return; }
    const g = new URLSearchParams(location.search).get("gmail");
    if (g) {
      history.replaceState(null, "", "/");
      const msg = { connected: ["Gmail connected. Reading booking emails now…"], denied: ["Gmail access was not granted.", 1], expired: ["The Gmail sign-in took too long. Try Connect Gmail again.", 1],
        failed: ["Google rejected the sign-in. Check the client ID, secret and redirect URI.", 1], "no-refresh": ["Google didn't return offline access. Remove the app at myaccount.google.com/permissions and connect again.", 1],
        "missing-client": ["Add the OAuth client ID and secret first.", 1], signin: ["Sign in, then connect Gmail again.", 1] }[g];
      if (msg) setTimeout(() => toast(msg[0], msg[1]), 300);
      if (g !== "connected") S.view = "settings";
    }
    try { await Promise.all([loadTrips(), loadTravellers()]); } catch (e) { toast(e.message, true); }
    render();
    // Auto-update: when the server installs a new version, offer a reload so this tab runs it too.
    let loaded = null;
    try { loaded = (await api("/version")).commit; } catch { /* ignore */ }
    setInterval(async () => {
      if (document.hidden || !loaded) return;
      try {
        const v = await api("/version");
        if (v.commit && v.commit !== loaded && !$("#updBar")) {
          const bar = document.createElement("div"); bar.id = "updBar"; bar.className = "upd-bar";
          bar.innerHTML = `<span>A new version of the travel desk was installed.</span><button class="btn sm primary" type="button">Reload now</button>`;
          bar.querySelector("button").addEventListener("click", () => location.reload());
          document.body.appendChild(bar);
        }
      } catch { /* offline */ }
    }, 120000);
    setInterval(async () => { if (document.hidden || $("#layer").innerHTML || S.view !== "trips") return; try { await loadTrips(); if (document.activeElement && document.activeElement.id === "q") renderTripList(); else renderTrips(); } catch { /* offline */ } }, 60000);
  }
  boot();
})();
