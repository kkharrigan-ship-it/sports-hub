// Sports Hub page. Reads data.json (written by each Refresh) and renders it.
// Everything personal (time zone, view, Watchlist, favourite Sports) stays in this browser.
// Watch options arrive already ranked, and the Event ids and length come from the
// Refresh, so this page and the calendar feeds always agree.
(function () {
  "use strict";

  const ZONES = { CST: "America/Chicago", ET: "America/New_York", GMT: "Europe/London", Local: undefined };
  const CATEGORIES = [
    { id: "all", label: "All" },
    { id: "ice", label: "🧊 Ice", name: "ice" },
    { id: "snow", label: "⛷️ Snow", name: "snow" },
    { id: "motor", label: "🏎️ Motor", name: "motor" },
    { id: "track", label: "🏃 Track & Other", name: "track & other" },
    { id: "aqua", label: "🏊 Aquatics", name: "aquatics" },
    { id: "rugby", label: "🏉 Rugby", name: "rugby" },
  ];
  const CATEGORY_IDS = new Set(CATEGORIES.map((c) => c.id).filter((id) => id !== "all"));
  const WATCH_LABELS = { have: "We have it", free: "Free", consider: "Paid (we don't have it)", vpn: "Free via VPN" };
  const EVENTS_SHOWN_PER_CARD = 4;
  // Fewer per "What's on" group on phones, where the groups stack.
  const horizonEventsShown = () => (matchMedia("(max-width: 720px)").matches ? 3 : 6);

  // A fixed clock for checking the page: ?now=2026-11-03T15:00:00Z
  const nowParam = new URLSearchParams(location.search).get("now");
  const NOW = nowParam ? new Date(nowParam) : new Date();

  // ---- Per-device storage (works, without persisting, when storage is blocked) ----
  const store = (() => {
    let ok = true;
    const memory = {};
    function get(key, fallback) {
      try {
        const raw = localStorage.getItem("sportsHub." + key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch (e) {
        ok = false;
        return key in memory ? memory[key] : fallback;
      }
    }
    function set(key, value) {
      memory[key] = value;
      try {
        localStorage.setItem("sportsHub." + key, JSON.stringify(value));
      } catch (e) {
        ok = false;
      }
    }
    return { get, set, get ok() { return ok; } };
  })();

  const state = {
    data: null,
    tz: store.get("tz", "CST"),
    view: store.get("view", "sports"),
    cat: "all",
    query: "",
    stars: store.get("stars", {}),          // Watchlist: eventKey -> saved copy of the Event
    favs: new Set(store.get("favs", [])),    // favourite Sport ids
    dismissed: new Set(store.get("dismissedReminders", [])),
    expanded: new Set(),
  };
  if (!(state.tz in ZONES)) state.tz = "CST";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  // Values used in class names and styles must be one of the known ones, never raw data.
  const safeCat = (sport) => (CATEGORY_IDS.has(sport.category) ? sport.category : "track");
  const safeType = (w) => (w.type in WATCH_LABELS ? w.type : "consider");
  const eventLengthMs = () => ((state.data && state.data.event_length_hours) || 2) * 3600e3;

  // ---- Dates and times ----
  function zoneOpts() { return ZONES[state.tz] ? { timeZone: ZONES[state.tz] } : {}; }
  function dayKeyOf(date) {
    // YYYY-MM-DD of an instant in the chosen zone.
    const parts = new Intl.DateTimeFormat("en-CA", { ...zoneOpts(), year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
    const v = (t) => parts.find((p) => p.type === t).value;
    return `${v("year")}-${v("month")}-${v("day")}`;
  }
  const todayKey = () => dayKeyOf(NOW);
  function addDays(key, n) {
    const d = new Date(key + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    return d.toISOString().slice(0, 10);
  }
  function fmtDay(key, withYear) {
    const d = new Date(key + "T12:00:00Z");
    return d.toLocaleDateString("en-US", { timeZone: "UTC", weekday: "short", month: "short", day: "numeric", ...(withYear ? { year: "numeric" } : {}) });
  }
  function fmtTime(date) {
    return date.toLocaleTimeString("en-US", { ...zoneOpts(), hour: "numeric", minute: "2-digit" });
  }
  // Day an Event falls on in the chosen zone (all-day Events keep their own date).
  function eventDay(ev) { return ev.start ? dayKeyOf(new Date(ev.start)) : ev.date; }
  function eventLastDay(ev) { return ev.start ? eventDay(ev) : (ev.end_date || ev.date); }
  function whenText(ev) {
    if (ev.start) return `${fmtDay(eventDay(ev))} · ${fmtTime(new Date(ev.start))}`;
    if (ev.end_date && ev.end_date !== ev.date) return `${fmtDay(ev.date)} – ${fmtDay(ev.end_date)}`;
    return fmtDay(ev.date);
  }
  function isLive(ev) {
    if (ev.start) {
      const start = new Date(ev.start).getTime();
      return NOW.getTime() >= start && NOW.getTime() < start + eventLengthMs();
    }
    const t = todayKey();
    return ev.date <= t && t <= (ev.end_date || ev.date);
  }
  const isOver = (ev) => (ev.start ? new Date(ev.start).getTime() + eventLengthMs() <= NOW.getTime() : eventLastDay(ev) < todayKey());
  const sortStamp = (ev) => ev.start || ev.date + "T00:00:00Z";

  // ---- Data helpers ----
  const eventKey = (sport, ev) => [sport.id, ev.name, ev.session || "", ev.date].join("|");
  const sportById = (id) => state.data.sports.find((s) => s.id === id);
  // A Sport for a starred Event whose Sport is no longer in data.json.
  const sportForSaved = (saved) => sportById(saved.sportId) || { id: saved.sportId, name: saved.sportName, category: "track", watch: [], events: [], status: "unavailable" };
  function matchesFilters(sport, ev) {
    if (state.cat !== "all" && sport.category !== state.cat) return false;
    if (!state.query) return true;
    const hay = [sport.name, ev && ev.name, ev && ev.session, ev && ev.location].join(" ").toLowerCase();
    return hay.includes(state.query);
  }
  function allEvents() {
    const out = [];
    for (const sport of state.data.sports) for (const ev of sport.events) out.push({ sport, ev });
    return out.sort((a, b) => sortStamp(a.ev).localeCompare(sortStamp(b.ev)));
  }
  const visibleEvents = () => allEvents().filter(({ sport, ev }) => !isOver(ev) && matchesFilters(sport, ev));
  const upcomingOf = (sport) => sport.events.filter((ev) => !isOver(ev));

  // ---- Small shared pieces of markup ----
  function badge(w) {
    const type = safeType(w);
    const title = [WATCH_LABELS[type], w.price, w.note].filter(Boolean).join(" · ");
    const label = type === "vpn" ? `${w.label} · VPN` : w.price ? `${w.label} ${w.price}` : w.label;
    return `<span class="s-badge s-${type}" title="${esc(title)}">${esc(label)}</span>`;
  }
  function catTag(sport) {
    const cat = CATEGORIES.find((c) => c.id === safeCat(sport));
    return `<span class="cat-tag cat-${cat.id}">${esc(cat.name)}</span>`;
  }
  const catColor = (sport) => `var(--${safeCat(sport)})`;
  const liveBadge = (ev) => (isLive(ev) ? '<span class="live-badge">LIVE</span>' : "");
  const eventTitle = (ev) => `<span class="ev-name">${esc(ev.name)}</span>${ev.session ? ` <span class="ev-session">· ${esc(ev.session)}</span>` : ""}`;
  const eventLine = (sport, ev) => `${esc(sport.name)}: ${esc(ev.name)}${ev.session ? ` · ${esc(ev.session)}` : ""}`;
  function eventActions(sport, ev) {
    const key = eventKey(sport, ev);
    const starred = key in state.stars;
    return `<div class="ev-actions">
      <button class="star-btn ev-star" data-star="${esc(key)}" aria-pressed="${starred}" aria-label="${starred ? "Remove from" : "Add to"} Watchlist: ${esc(ev.name)}">${starred ? "★" : "☆"}</button>
      <button class="add-btn" data-add="${esc(key)}" aria-label="Add ${esc(ev.name)} to your calendar">+ cal</button>
    </div>`;
  }

  // ---- Calendar files made in the browser (single Event, Watchlist) ----
  const icsStamp = (d) => d.toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  function icsDates(ev) {
    if (ev.start) {
      const s = new Date(ev.start);
      return [`DTSTART:${icsStamp(s)}`, `DTEND:${icsStamp(new Date(s.getTime() + eventLengthMs()))}`];
    }
    const compact = (d) => d.replace(/-/g, "");
    return [`DTSTART;VALUE=DATE:${compact(ev.date)}`, `DTEND;VALUE=DATE:${compact(addDays(ev.end_date || ev.date, 1))}`];
  }
  const icsText = (s) => String(s).replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/[,;]/g, (c) => "\\" + c);
  // iCal lines may be at most 75 bytes; longer ones continue on lines starting with a space.
  function icsFold(line) {
    const bytes = new TextEncoder();
    const out = [];
    let current = "";
    for (const ch of line) {
      if (bytes.encode(current + ch).length > (out.length ? 74 : 75)) {
        out.push(current);
        current = "";
      }
      current += ch;
    }
    out.push(current);
    return out.join("\r\n ");
  }
  function icsFor(items) {
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sports Hub//sports-hub//EN"];
    for (const { sport, ev } of items) {
      const watch = sport.watch[0];
      const description = [ev.session, ev.location, watch && "Watch: " + watch.label].filter(Boolean).join("\n");
      lines.push(
        "BEGIN:VEVENT",
        `UID:${icsText(ev.uid || eventKey(sport, ev) + "@sports-hub")}`,  // the same id the subscription feeds use
        `DTSTAMP:${icsStamp(new Date())}`,
        `SUMMARY:${icsText(`${sport.name}: ${ev.name}${ev.session ? ` (${ev.session})` : ""}`)}`,
        ...icsDates(ev),
        ...(ev.location ? [`LOCATION:${icsText(ev.location)}`] : []),
        ...(description ? [`DESCRIPTION:${icsText(description)}`] : []),
        "END:VEVENT",
      );
    }
    lines.push("END:VCALENDAR");
    return lines.map(icsFold).join("\r\n") + "\r\n";
  }
  function download(name, text) {
    const url = URL.createObjectURL(new Blob([text], { type: "text/calendar" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  // Calendar apps subscribe with webcal://. Only the Hub's own feed paths are linked.
  function subscribeUrl(sport) {
    if (!/^feeds\/[a-z0-9-]+\.ics$/.test(sport.feed || "")) return "#";
    const url = new URL(sport.feed, location.href);
    return /^https?:$/.test(url.protocol) ? url.href.replace(/^https?:/, "webcal:") : sport.feed;
  }

  // ---- Rendering ----
  function eventRow(sport, ev) {
    const tags = (ev.tags || []).map((t) => `<span class="tag${t === "slam" ? " tag-slam" : ""}">${t === "slam" ? "Grand Slam" : esc(t)}</span>`).join("");
    return `<div class="ev-row">
      <div class="ev-when">${esc(whenText(ev))}${liveBadge(ev)}</div>
      <div class="ev-body">
        <div>${eventTitle(ev)}${tags ? `<span class="ev-tags">${tags}</span>` : ""}</div>
        ${ev.location ? `<div class="ev-loc">${esc(ev.location)}</div>` : ""}
        ${ev.stale_since ? `<div class="stale-note">stale since ${esc(fmtDay(ev.stale_since, true))}</div>` : ""}
      </div>
      ${eventActions(sport, ev)}
    </div>`;
  }

  function sportCard(sport) {
    const events = upcomingOf(sport).filter((ev) => matchesFilters(sport, ev));
    const expanded = state.expanded.has(sport.id);
    const shown = expanded ? events : events.slice(0, EVENTS_SHOWN_PER_CARD);
    const fav = state.favs.has(sport.id);
    const notes = sport.watch.filter((w) => w.note).map((w) => `${esc(w.label)}: ${esc(w.note)}`).join(" · ");
    return `<article class="sport-card${fav ? " is-fav" : ""}" aria-label="${esc(sport.name)}">
      <div class="card-head">
        <div class="card-top">
          <h3 class="sport-name">${esc(sport.name)}</h3>
          ${catTag(sport)}
          <button class="star-btn" data-fav="${esc(sport.id)}" aria-pressed="${fav}" aria-label="${fav ? "Unpin" : "Pin"} ${esc(sport.name)} as a favourite">${fav ? "★" : "☆"}</button>
        </div>
        <div class="badges">${sport.watch.map(badge).join("")}${sport.rights_unconfirmed ? '<span class="s-badge s-recheck" title="This season\'s TV deal wasn\'t confirmed when researched">Recheck before the season</span>' : ""}</div>
        ${notes ? `<div class="watch-notes">${notes}</div>` : ""}
        ${sport.stale_since ? `<div class="stale-note">Some Events are stale since ${esc(fmtDay(sport.stale_since, true))}: their source couldn't be reached.</div>` : ""}
      </div>
      ${shown.map((ev) => eventRow(sport, ev)).join("")}
      ${events.length > EVENTS_SHOWN_PER_CARD ? `<button class="show-more" data-expand="${esc(sport.id)}">${expanded ? "Show fewer" : `Show all ${events.length} Events`}</button>` : ""}
      <div class="card-links">
        <a class="mini-btn" href="${esc(subscribeUrl(sport))}" title="Subscribe in your calendar app; it stays up to date">📅 Subscribe</a>
      </div>
    </article>`;
  }

  function chip(sport, status, note) {
    return `<div class="offseason-chip">
      <div><span class="chip-name">${esc(sport.name)}</span> <span class="return">${esc(status)}</span></div>
      ${note ? `<div class="chip-note">${esc(note)}</div>` : ""}
    </div>`;
  }

  function renderSports() {
    const sports = state.data.sports.filter((s) => state.cat === "all" || s.category === state.cat);
    // In season with something still to come (Events can pass between Refreshes).
    const active = sports.filter((s) => s.status === "in-season" && upcomingOf(s).length);
    const withMatches = active.filter((s) => !state.query || upcomingOf(s).some((ev) => matchesFilters(s, ev)));
    const ordered = [...withMatches.filter((s) => state.favs.has(s.id)), ...withMatches.filter((s) => !state.favs.has(s.id))];
    $("sportGrid").innerHTML = ordered.map(sportCard).join("");

    const named = (s) => !state.query || matchesFilters(s, null);
    const resting = sports.filter((s) => named(s) && (s.status === "off-season" || (s.status === "in-season" && !upcomingOf(s).length)));
    const down = sports.filter((s) => named(s) && s.status === "unavailable");
    $("offseason").innerHTML =
      (resting.length ? `<h2 class="section-title">Between seasons</h2><div class="offseason-chips">${resting
        .map((s) => (s.status === "off-season" ? chip(s, s.returns || "Dates TBA", s.note) : chip(s, "More dates at the next Refresh")))
        .join("")}</div>` : "") +
      (down.length ? `<h2 class="section-title">Source unavailable right now</h2><div class="offseason-chips">${down
        .map((s) => chip(s, "Check the official site", "Its data source couldn't be reached at the last Refresh; it should be back next time."))
        .join("")}</div>` : "");
    return ordered.length + resting.length + down.length;
  }

  function renderTimeline() {
    const byDay = new Map();
    for (const item of visibleEvents()) {
      const key = eventDay(item.ev) < todayKey() ? todayKey() : eventDay(item.ev); // running multi-day Events sit on today
      if (!byDay.has(key)) byDay.set(key, []);
      byDay.get(key).push(item);
    }
    $("timeline").innerHTML = [...byDay.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([day, items]) => `<div>
        <div class="tl-day-head">${esc(fmtDay(day))}${day === todayKey() ? '<span class="today-pill">Today</span>' : ""}</div>
        <div class="tl-events">${items.map(({ sport, ev }) => timelineRow(sport, ev)).join("")}</div>
      </div>`)
      .join("");
    return byDay.size;
  }

  function timelineRow(sport, ev, note) {
    const time = ev.start ? fmtTime(new Date(ev.start)) : ev.end_date && ev.end_date !== ev.date ? "multi-day" : "all day";
    return `<div class="tl-ev">
      <div class="tl-time">${esc(time)}${isLive(ev) ? "<br>" + liveBadge(ev) : ""}</div>
      <div class="tl-sport" style="color:${catColor(sport)}">${esc(sport.name)}</div>
      <div class="tl-main">${eventTitle(ev)}${ev.location ? `<div class="ev-loc">${esc(ev.location)}</div>` : ""}${note ? `<div class="tl-note">${esc(note)}</div>` : ""}</div>
      ${eventActions(sport, ev)}
    </div>`;
  }

  // Why a starred Event isn't in today's data.json, in plain words (or null if it is, or if absence means nothing).
  function missingReason(sport, ev, listed) {
    if (listed) return null;
    if (sport.status === "unavailable") return "Its source couldn't be reached at the last Refresh; check the official site.";
    // data.json only covers the next 56 days (or next 6 Events), so absence beyond that range is expected.
    const covered = sport.events.map((e) => e.end_date || e.date).sort().pop();
    if (!covered || ev.date > covered) return null;
    return "No longer listed by its source: it may have moved or been cancelled.";
  }

  function watchlistItems() {
    const listed = new Map(allEvents().map((item) => [eventKey(item.sport, item.ev), item]));
    const items = [];
    for (const [key, saved] of Object.entries(state.stars)) {
      const current = listed.get(key);
      const sport = current ? current.sport : sportForSaved(saved);
      const ev = current ? current.ev : saved.event;
      if (isOver(ev) || !matchesFilters(sport, ev)) continue;
      items.push({ sport, ev, note: missingReason(sport, ev, Boolean(current)) });
    }
    return items.sort((a, b) => sortStamp(a.ev).localeCompare(sortStamp(b.ev)));
  }

  function renderWatchlist() {
    const items = watchlistItems();
    $("watchlist").innerHTML = items.length
      ? `<div class="tl-events">${items.map(({ sport, ev, note }) => `<div class="${note ? "unlisted" : ""}">${timelineRow(sport, ev, note)}</div>`).join("")}</div>`
      : `<div class="empty">Nothing starred yet. Tap ☆ on any Event and it'll show up here.</div>`;
    $("exportWatchlist").disabled = !items.length;
    return 1; // an empty Watchlist explains itself, so it's never "no matches"
  }

  function renderHorizons() {
    const today = todayKey();
    const dow = new Date(today + "T12:00:00Z").getUTCDay(); // 0 Sun ... 6 Sat
    const sat = dow === 0 ? addDays(today, -1) : addDays(today, 6 - dow);
    const buckets = [
      { label: "This Weekend", from: dow === 0 || dow === 6 ? today : sat, to: addDays(sat, 1), empty: "A quiet weekend. Time for a walk?" },
      { label: "Next 7 Days", from: today, to: addDays(today, 6), empty: "Nothing this week. Rest up!" },
      { label: "Next 14 Days", from: today, to: addDays(today, 13), empty: "Two quiet weeks ahead." },
    ];
    const events = visibleEvents();
    $("horizons").innerHTML = buckets.map((b) => {
      const inside = events.filter(({ ev }) => eventDay(ev) <= b.to && eventLastDay(ev) >= b.from);
      const shown = inside.slice(0, horizonEventsShown());
      return `<div class="horizon-bucket">
        <div class="horizon-head"><span class="horizon-label">${b.label}</span><span class="horizon-count">${inside.length} Event${inside.length === 1 ? "" : "s"}</span></div>
        ${inside.length ? `<div class="horizon-events">${shown.map(({ sport, ev }) => `<div class="horizon-ev">
            <span class="horizon-ev-dot" style="background:${catColor(sport)}" aria-hidden="true"></span>
            <div class="horizon-ev-body">
              <div class="horizon-ev-name" title="${eventLine(sport, ev)}">${eventLine(sport, ev)}</div>
              <div class="horizon-ev-meta">${esc(whenText(ev))}${liveBadge(ev)}</div>
            </div></div>`).join("")}</div>
          ${inside.length > shown.length ? `<div class="horizon-more">+${inside.length - shown.length} more</div>` : ""}`
        : `<div class="horizon-empty">${b.empty}</div>`}
      </div>`;
    }).join("");
  }

  function renderBanners() {
    const live = visibleEvents().filter(({ ev }) => isLive(ev));
    $("liveBanner").classList.toggle("hidden", !live.length);
    $("liveBanner").innerHTML = live.length
      ? `<span class="live-tag">LIVE</span> ${live.slice(0, 4).map(({ sport, ev }) => `<span>${eventLine(sport, ev)}</span>`).join(" · ")}${live.length > 4 ? ` · +${live.length - 4} more` : ""}`
      : "";

    const today = todayKey();
    const reminder = (state.data.reminders || []).find((r) => r.show_from <= today && today <= r.end_date && !state.dismissed.has(r.id));
    $("reminder").classList.toggle("hidden", !reminder);
    if (reminder) {
      const started = reminder.date <= today;
      $("reminder").innerHTML = `<span>📺 <strong>${esc(reminder.name)}</strong> ${started ? "is on now, to " + esc(fmtDay(reminder.end_date)) : `runs ${esc(fmtDay(reminder.date))} – ${esc(fmtDay(reminder.end_date))}`}. Time to switch ESPN+ on for this month's Grand Slam.</span>
        <button class="banner-close" data-dismiss="${esc(reminder.id)}" aria-label="Dismiss the ESPN+ reminder for ${esc(reminder.name)}">Got it</button>`;
    }
  }

  function renderControls() {
    document.querySelectorAll(".tz-btn").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tz === state.tz)));
    document.querySelectorAll(".view-tab").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.view)));
    $("catFilter").innerHTML = CATEGORIES.map((c) => `<button class="cat-pill pill-${c.id}" data-cat="${c.id}" aria-pressed="${state.cat === c.id}">${esc(c.label)}</button>`).join("");
    for (const v of ["sports", "timeline", "watchlist"]) $("view-" + v).classList.toggle("hidden", state.view !== v);
    $("legend").innerHTML = Object.keys(WATCH_LABELS).map((t) => `<div class="leg"><span class="leg-dot leg-${t}" aria-hidden="true"></span>${WATCH_LABELS[t]}</div>`).join("") +
      '<div class="leg"><span class="leg-dot leg-recheck" aria-hidden="true"></span>Recheck before the season</div>';
  }

  function render() {
    if (!state.data) return;
    renderControls();
    renderBanners();
    renderHorizons();
    const count = state.view === "sports" ? renderSports() : state.view === "timeline" ? renderTimeline() : renderWatchlist();
    $("noMatches").classList.toggle("hidden", count > 0);
  }

  // ---- Interaction ----
  function findItem(key) {
    const listed = allEvents().find((item) => eventKey(item.sport, item.ev) === key);
    if (listed) return listed;
    const saved = state.stars[key];
    return saved ? { sport: sportForSaved(saved), ev: saved.event } : null;
  }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("button");
    if (!t) return;
    const d = t.dataset;
    if (d.tz) { state.tz = d.tz; store.set("tz", state.tz); }
    else if (d.view) { state.view = d.view; store.set("view", state.view); }
    else if (d.cat) { state.cat = d.cat; }
    else if (d.fav) {
      state.favs.has(d.fav) ? state.favs.delete(d.fav) : state.favs.add(d.fav);
      store.set("favs", [...state.favs]);
      warnIfNotSaved();
    } else if (d.star) {
      if (d.star in state.stars) delete state.stars[d.star];
      else {
        const item = findItem(d.star);
        if (item) state.stars[d.star] = { sportId: item.sport.id, sportName: item.sport.name, event: item.ev };
      }
      store.set("stars", state.stars);
      warnIfNotSaved();
    } else if (d.add) {
      const item = findItem(d.add);
      if (item) download(`${item.sport.id}-${item.ev.date}.ics`, icsFor([item]));
      return;
    } else if (d.expand) {
      state.expanded.has(d.expand) ? state.expanded.delete(d.expand) : state.expanded.add(d.expand);
    } else if (d.dismiss) {
      state.dismissed.add(d.dismiss);
      store.set("dismissedReminders", [...state.dismissed]);
    } else if (t.id === "exportWatchlist") {
      download("sports-hub-watchlist.ics", icsFor(watchlistItems()));
      return;
    } else if (t.id === "clearFilters") {
      state.cat = "all";
      state.query = "";
      $("search").value = "";
    } else return;
    render();
  });

  $("search").addEventListener("input", (e) => {
    state.query = e.target.value.trim().toLowerCase();
    render();
  });

  let warned = false;
  function warnIfNotSaved() {
    if (store.ok || warned) return;
    warned = true;
    $("notice").textContent = "This browser isn't letting the Hub save, so stars and settings will reset when you close the page.";
    $("notice").classList.remove("hidden");
  }

  // ---- Start ----
  fetch("data.json", { cache: "no-cache" })
    .then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then((data) => {
      state.data = data;
      $("updated").textContent = `Updated ${fmtDay(data.last_updated, true)}`;
      render();
      warnIfNotSaved();
    })
    .catch(() => {
      $("updated").textContent = "Couldn't load the schedule.";
      $("notice").textContent = "The Hub's data didn't load. Try refreshing the page in a minute.";
      $("notice").classList.remove("hidden");
    });
})();
