// Shared plumbing: templating, live updates, data fetching, routing, preferences.
import { h } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import htm from "htm";

export const html = htm.bind(h);

// -- preferences (localStorage; the server keeps no UI state) --

const PREFIX = "openspeccer:";

export function pref(key, fallback) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function setPref(key, value) {
  localStorage.setItem(PREFIX + key, JSON.stringify(value));
  emit();
}

// -- live state: the server's version counter over SSE --

export const live = { version: 0, status: "connecting", at: null };
const listeners = new Set();

function emit() {
  for (const fn of listeners) fn();
}

export function useLive() {
  const [, force] = useState(0);
  useEffect(() => {
    const fn = () => force((n) => n + 1);
    listeners.add(fn);
    return () => listeners.delete(fn);
  }, []);
  return live;
}

export function connectLive() {
  const es = new EventSource("/api/events");
  es.addEventListener("version", (e) => {
    live.version = Number(e.data);
    live.status = "live";
    live.at = new Date();
    emit();
  });
  es.onopen = () => {
    live.status = "live";
    emit();
  };
  es.onerror = () => {
    live.status = "offline";
    emit();
  };
}

// -- data --

export function scopeParams() {
  const scope = pref("scope", "worktrees");
  const p = new URLSearchParams();
  p.set("aggregate", scope === "main" ? "0" : "1");
  p.set("jj", scope === "jj" ? "1" : "0");
  return p;
}

export function apiUrl(path, params = {}) {
  const p = scopeParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") p.set(k, v);
  return `/api/${path}?${p}`;
}

// Fetches JSON and refetches whenever the repo changes. Keeps the previous data while
// refetching, so a live update never flashes a loading state.
export function useApi(url) {
  const { version } = useLive();
  const [state, setState] = useState({ data: null, error: null, url: null });
  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    fetch(url)
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
        return body;
      })
      .then((data) => !cancelled && setState({ data, error: null, url }))
      .catch((error) => !cancelled && setState((s) => ({ data: s.url === url ? s.data : null, error, url })));
    return () => {
      cancelled = true;
    };
  }, [url, version]);
  const stale = state.url !== url;
  return { data: stale ? null : state.data, error: stale ? null : state.error, loading: stale || (!state.data && !state.error) };
}

// -- routing: #/section/rest?query --

export function parseHash() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [path, query = ""] = raw.split("?");
  return { parts: path.split("/").filter(Boolean).map(decodeURIComponent), query: new URLSearchParams(query) };
}

export function useRoute() {
  const [route, setRoute] = useState(parseHash);
  useEffect(() => {
    const fn = () => setRoute(parseHash());
    addEventListener("hashchange", fn);
    return () => removeEventListener("hashchange", fn);
  }, []);
  return route;
}

export function href(parts, query = {}) {
  const path = parts.map((p) => p.split("/").map(encodeURIComponent).join("/")).join("/");
  const q = new URLSearchParams(Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== ""));
  const qs = q.toString();
  return `#/${path}${qs ? `?${qs}` : ""}`;
}

export function setQuery(updates) {
  const { parts, query } = parseHash();
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") query.delete(k);
    else query.set(k, v);
  }
  const qs = query.toString();
  history.replaceState(null, "", `#/${parts.map(encodeURIComponent).join("/")}${qs ? `?${qs}` : ""}`);
  dispatchEvent(new HashChangeEvent("hashchange"));
}

// -- formatting --

export function daysAgo(iso) {
  if (!iso) return null;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
}

export function relative(iso) {
  const d = daysAgo(iso);
  if (d === null) return "";
  if (d <= 0) return "today";
  if (d === 1) return "yesterday";
  if (d < 60) return `${d}d ago`;
  return iso.slice(0, 10);
}

export function changeHref(c, tab) {
  const query = { tab };
  if (c.source && !c.source.is_main) query.wt = c.source.key;
  return href(["changes", c.slug], query);
}

export function useWidth(ref) {
  const [width, setWidth] = useState(800);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [ref.current]);
  return width;
}

export { useEffect, useRef, useState };
