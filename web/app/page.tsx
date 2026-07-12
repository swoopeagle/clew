"use client";

import {
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { useSearchParams } from "next/navigation";

type Prospect = {
  id: number;
  name: string;
  program_area?: string | null;
  geography?: string | null;
  grant_size?: string | null;
  fit_rationale?: string | null;
  fit_sources?: string | null;
  warm_path_note?: string | null;
  deadline_date?: string | null;
  report_due_date?: string | null;
  reported_at?: string | null;
};

type BoardData = {
  org_profile: {
    mission?: string | null;
    geography?: string | null;
    program_areas?: string | null;
    grant_size_min?: number | null;
    grant_size_max?: number | null;
  } | null;
  board: Record<string, Prospect[]>;
  pipeline: Record<string, number>;
  tasks?: Record<string, { open: number; done: number }>;
  generated_at: string;
};

const STAGES: { key: string; label: string; emoji: string }[] = [
  { key: "qualified", label: "Qualified", emoji: "🔍" },
  { key: "approved", label: "Approved", emoji: "✅" },
  { key: "applied", label: "Applied", emoji: "✍️" },
  { key: "submitted", label: "Submitted", emoji: "📮" },
  { key: "awarded", label: "Awarded", emoji: "🏆" },
  { key: "declined", label: "Declined", emoji: "❌" },
  { key: "passed", label: "Passed", emoji: "⏭️" },
];

const ACTIVE_STAGES = ["qualified", "approved", "applied", "submitted"];

// Archimedean spiral, precomputed — the thread that names the product,
// drawn on load by animating stroke-dashoffset (pathLength normalizes it).
const SPIRAL_PATH =
  "M32.0 29.0 L32.4 28.8 L32.9 28.7 L33.4 28.7 L34.0 28.8 L34.5 28.9 L35.0 29.2 L35.5 29.5 L36.0 29.9 L36.4 30.4 L36.8 31.0 L37.1 31.6 L37.3 32.3 L37.4 33.1 L37.4 33.9 L37.2 34.7 L37.0 35.5 L36.6 36.2 L36.1 37.0 L35.5 37.6 L34.8 38.2 L34.0 38.7 L33.1 39.1 L32.1 39.4 L31.0 39.5 L30.0 39.5 L28.9 39.4 L27.8 39.0 L26.8 38.6 L25.8 37.9 L24.9 37.1 L24.1 36.2 L23.4 35.2 L22.9 34.0 L22.5 32.8 L22.3 31.5 L22.3 30.1 L22.4 28.8 L22.8 27.4 L23.3 26.1 L24.1 24.9 L25.0 23.7 L26.1 22.7 L27.3 21.8 L28.7 21.1 L30.2 20.5 L31.8 20.2 L33.4 20.1 L35.0 20.2 L36.7 20.5 L38.3 21.1 L39.8 21.9 L41.3 22.9 L42.6 24.2 L43.7 25.6 L44.6 27.1 L45.4 28.9 L45.9 30.7 L46.1 32.6 L46.1 34.5 L45.8 36.5 L45.2 38.4 L44.4 40.2 L43.3 42.0 L42.0 43.6 L40.4 45.0 L38.7 46.2 L36.7 47.1 L34.7 47.8 L32.5 48.2 L30.3 48.3 L28.0 48.1 L25.8 47.6 L23.7 46.8 L21.6 45.7 L19.7 44.3 L18.0 42.6 L16.5 40.7 L15.3 38.6 L14.4 36.3 L13.8 33.9 L13.5 31.4 L13.5 28.9 L14.0 26.3 L14.7 23.9 L15.8 21.5 L17.3 19.3 L19.0 17.2 L21.0 15.5 L23.3 13.9 L25.7 12.7 L28.4 11.9 L31.1 11.4 L34.0 11.3 L36.8 11.5 L39.6 12.2 L42.3 13.2 L44.9 14.7 L47.2 16.4 L49.4 18.5 L51.2 20.9 L52.7 23.6 L53.8 26.4 L54.6 29.4 L54.9 32.5 L54.8 35.6 L54.3 38.7 L53.4 41.8 L52.0 44.7 L50.2 47.4 L48.1 49.9 L45.6 52.1 L42.9 53.9 L39.9 55.4 L36.7 56.4 L33.3 57.0 L29.9 57.1 L26.5 56.8 L23.1 56.0 L19.8 54.7 L16.7 53.0";

function SpiralLogo() {
  return (
    <svg
      className="spiral"
      viewBox="0 0 68 68"
      width="44"
      height="44"
      aria-hidden
      role="presentation"
    >
      <path
        d={SPIRAL_PATH}
        pathLength={1}
        fill="none"
        stroke="currentColor"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function useCountUp(target: number, ready: boolean): number {
  const [shown, setShown] = useState(0);
  const fromRef = useRef(0);
  useEffect(() => {
    if (!ready) return;
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const from = fromRef.current;
    if (reduced || from === target) {
      setShown(target);
      fromRef.current = target;
      return;
    }
    const start = performance.now();
    const duration = 750;
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(Math.round(from + (target - from) * eased));
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        fromRef.current = target;
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ready]);
  return shown;
}

function parseSources(raw?: string | null): string[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function sourceLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "source";
  }
}

function daysUntil(iso?: string | null): number | null {
  if (!iso) return null;
  const due = new Date(`${iso}T00:00:00`);
  if (isNaN(due.getTime())) return null;
  return Math.ceil((due.getTime() - Date.now()) / 86_400_000);
}

function grantRange(profile: BoardData["org_profile"]): string | null {
  if (!profile) return null;
  const { grant_size_min: lo, grant_size_max: hi } = profile;
  if (lo == null && hi == null) return null;
  const fmt = (n: number) => `$${n.toLocaleString()}`;
  if (lo != null && hi != null) return `${fmt(lo)} – ${fmt(hi)}`;
  return lo != null ? `${fmt(lo)}+` : `up to ${fmt(hi!)}`;
}

function delayStyle(index: number): CSSProperties {
  return { "--d": `${Math.min(index, 8) * 70}ms` } as CSSProperties;
}

function Tile({
  value,
  label,
  ready,
  accent,
  index,
}: {
  value: number;
  label: string;
  ready: boolean;
  accent?: boolean;
  index: number;
}) {
  const shown = useCountUp(value, ready);
  return (
    <div className={accent ? "tile accent rise" : "tile rise"} style={delayStyle(index)}>
      <span className="tile-number">{shown}</span>
      <span className="tile-label">{label}</span>
    </div>
  );
}

function ProspectCard({
  prospect,
  stage,
  index,
  taskCounts,
}: {
  prospect: Prospect;
  stage: string;
  index: number;
  taskCounts?: { open: number; done: number };
}) {
  const sources = parseSources(prospect.fit_sources);
  const days = stage === "approved" ? daysUntil(prospect.deadline_date) : null;
  const dueSoon = days !== null && days >= 0 && days <= 7;
  const totalTasks = (taskCounts?.open ?? 0) + (taskCounts?.done ?? 0);

  return (
    <article className="card rise" style={delayStyle(index)}>
      <h4>{prospect.name}</h4>
      {((prospect.deadline_date && stage === "approved") || totalTasks > 0) && (
        <p className="chip-row">
          {prospect.deadline_date && stage === "approved" && (
            <span className={dueSoon ? "chip chip-urgent" : "chip chip-date"}>
              {dueSoon ? "⏰" : "📅"} {prospect.deadline_date}
              {days !== null && days >= 0 && ` · ${days}d left`}
            </span>
          )}
          {totalTasks > 0 && (
            <span className="chip chip-tasks">
              🧩 {taskCounts!.done}/{totalTasks} tasks
            </span>
          )}
        </p>
      )}
      {prospect.grant_size && <p className="meta">💰 {prospect.grant_size}</p>}
      {prospect.geography && <p className="meta">📍 {prospect.geography}</p>}
      {prospect.fit_rationale && (
        <p className="rationale">{prospect.fit_rationale}</p>
      )}
      {prospect.warm_path_note && (
        <p className="warm">🧶 {prospect.warm_path_note}</p>
      )}
      {sources.length > 0 && (
        <p className="chip-row">
          {sources.map((s) =>
            s.startsWith("http") ? (
              <a
                className="chip chip-source"
                key={s}
                href={s}
                target="_blank"
                rel="noopener noreferrer"
              >
                📎 {sourceLabel(s)}
              </a>
            ) : (
              <span className="chip chip-source" key={s}>
                📎 {s}
              </span>
            ),
          )}
        </p>
      )}
    </article>
  );
}

function Skeleton() {
  return (
    <>
      <section className="tiles" aria-hidden>
        {[0, 1, 2, 3].map((i) => (
          <div className="tile skeleton" key={i} style={delayStyle(i)}>
            <span className="skeleton-bar wide" />
            <span className="skeleton-bar" />
          </div>
        ))}
      </section>
      <section className="columns" aria-label="Loading the board">
        {[0, 1, 2, 3].map((i) => (
          <div className="column" key={i}>
            <div className="skeleton-bar head" />
            <div className="card skeleton tall" />
            {i < 2 && <div className="card skeleton tall" />}
          </div>
        ))}
      </section>
    </>
  );
}

function Board() {
  const [data, setData] = useState<BoardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const org = searchParams.get("org") ?? "";
  const sig = searchParams.get("sig") ?? "";

  const load = useCallback(async () => {
    try {
      const qs = new URLSearchParams();
      if (org) qs.set("org", org);
      if (sig) qs.set("sig", sig);
      const res = await fetch(`/api/board?${qs}`, { cache: "no-store" });
      if (res.status === 403) {
        throw new Error(
          "This board link isn't valid — grab a fresh link from Clew in your Slack (the 🌐 Web Board button).",
        );
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `HTTP ${res.status}`);
      }
      setData(await res.json());
      setError(null);
      setUpdatedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [org, sig]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 15_000);
    return () => clearInterval(timer);
  }, [load]);

  const ready = data !== null;
  const pipeline = data?.pipeline ?? {};
  const activeCount = ACTIVE_STAGES.reduce(
    (sum, s) => sum + (pipeline[s] ?? 0),
    0,
  );
  const range = grantRange(data?.org_profile ?? null);

  return (
    <main>
      <div className="backdrop" aria-hidden />
      <header className="hero">
        <div className="hero-brand">
          <SpiralLogo />
          <h1>
            Clew <span className="hero-sep">·</span> Grant Board
          </h1>
        </div>
        <div className="hero-meta">
          {updatedAt && (
            <span className="live">
              <span className="live-dot" aria-hidden />
              Live · updated {updatedAt}
            </span>
          )}
        </div>
      </header>

      {error && (
        <div className="banner rise" role="alert">
          ⚠️ {error} — is the Clew Slack app running?
        </div>
      )}

      {data?.org_profile && (
        <section className="profile rise">
          <h2>{data.org_profile.mission}</h2>
          <p className="meta">
            {data.org_profile.geography && (
              <>📍 {data.org_profile.geography}</>
            )}
            {data.org_profile.program_areas && (
              <> &nbsp;·&nbsp; 🎯 {data.org_profile.program_areas}</>
            )}
            {range && <> &nbsp;·&nbsp; 💰 {range}</>}
          </p>
        </section>
      )}

      {!ready && !error && <Skeleton />}

      {ready && (
        <>
          <section className="tiles" aria-label="Pipeline summary">
            <Tile
              value={activeCount}
              label="Active prospects"
              ready={ready}
              index={0}
            />
            <Tile
              value={pipeline.approved ?? 0}
              label="Approved"
              ready={ready}
              index={1}
            />
            <Tile
              value={pipeline.submitted ?? 0}
              label="Awaiting decision"
              ready={ready}
              index={2}
            />
            <Tile
              value={pipeline.awarded ?? 0}
              label="🏆 Awarded"
              ready={ready}
              accent
              index={3}
            />
          </section>

          <section className="columns" aria-label="Grant board by stage">
            {STAGES.map(({ key, label, emoji }) => {
              const items = data?.board?.[key] ?? [];
              if (items.length === 0 && ["declined", "passed"].includes(key)) {
                return null;
              }
              return (
                <div className={`column stage-${key}`} key={key}>
                  <h3>
                    <span aria-hidden>{emoji}</span> {label}
                    <span className="count">{items.length}</span>
                  </h3>
                  {items.length === 0 ? (
                    <p className="empty">
                      {key === "qualified"
                        ? "🧶 Nothing here yet — ask Clew to find grants in Slack."
                        : "—"}
                    </p>
                  ) : (
                    items.map((p, i) => (
                      <ProspectCard
                        key={p.id}
                        prospect={p}
                        stage={key}
                        index={i}
                        taskCounts={data?.tasks?.[String(p.id)]}
                      />
                    ))
                  )}
                </div>
              );
            })}
          </section>
        </>
      )}

      <footer>
        Actions happen in Slack — approve, pass, and track grants by talking to{" "}
        <strong>@Clew</strong>. This board is the live, read-only view of that
        same pipeline.
      </footer>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense>
      <Board />
    </Suspense>
  );
}
