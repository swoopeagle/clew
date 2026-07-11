"use client";

import { useCallback, useEffect, useState } from "react";

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

function ProspectCard({
  prospect,
  stage,
}: {
  prospect: Prospect;
  stage: string;
}) {
  const sources = parseSources(prospect.fit_sources);
  const days = stage === "approved" ? daysUntil(prospect.deadline_date) : null;
  const dueSoon = days !== null && days >= 0 && days <= 7;

  return (
    <article className="card">
      <h4>{prospect.name}</h4>
      {prospect.deadline_date && stage === "approved" && (
        <p className={dueSoon ? "deadline urgent" : "deadline"}>
          {dueSoon ? "⏰ Due soon — " : "📅 "}
          {prospect.deadline_date}
          {days !== null && days >= 0 && ` · ${days}d left`}
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
        <p className="sources">
          📎{" "}
          {sources.map((s, i) => (
            <span key={s}>
              {i > 0 && " · "}
              {s.startsWith("http") ? (
                <a href={s} target="_blank" rel="noopener noreferrer">
                  {sourceLabel(s)}
                </a>
              ) : (
                s
              )}
            </span>
          ))}
        </p>
      )}
    </article>
  );
}

export default function Home() {
  const [data, setData] = useState<BoardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/board", { cache: "no-store" });
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
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 15_000);
    return () => clearInterval(timer);
  }, [load]);

  const pipeline = data?.pipeline ?? {};
  const activeCount = ACTIVE_STAGES.reduce(
    (sum, s) => sum + (pipeline[s] ?? 0),
    0,
  );
  const range = grantRange(data?.org_profile ?? null);

  return (
    <main>
      <header className="hero">
        <div>
          <h1>
            <span aria-hidden>🧵</span> Clew — Grant Board
          </h1>
          <p className="tagline">
            Every prospect cited — Clew never fabricates a funder.
          </p>
        </div>
        <div className="hero-meta">
          {updatedAt && <span>Live · updated {updatedAt}</span>}
        </div>
      </header>

      {error && (
        <div className="banner" role="alert">
          ⚠️ {error} — is the Clew Slack app running?
        </div>
      )}

      {data?.org_profile && (
        <section className="profile">
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

      <section className="tiles" aria-label="Pipeline summary">
        <div className="tile">
          <span className="tile-number">{activeCount}</span>
          <span className="tile-label">Active prospects</span>
        </div>
        <div className="tile">
          <span className="tile-number">{pipeline.approved ?? 0}</span>
          <span className="tile-label">Approved</span>
        </div>
        <div className="tile">
          <span className="tile-number">{pipeline.submitted ?? 0}</span>
          <span className="tile-label">Awaiting decision</span>
        </div>
        <div className="tile accent">
          <span className="tile-number">{pipeline.awarded ?? 0}</span>
          <span className="tile-label">🏆 Awarded</span>
        </div>
      </section>

      <section className="columns" aria-label="Grant board by stage">
        {STAGES.map(({ key, label, emoji }) => {
          const items = data?.board?.[key] ?? [];
          if (items.length === 0 && ["declined", "passed"].includes(key)) {
            return null;
          }
          return (
            <div className="column" key={key}>
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
                items.map((p) => (
                  <ProspectCard key={p.id} prospect={p} stage={key} />
                ))
              )}
            </div>
          );
        })}
      </section>

      <footer>
        Actions happen in Slack — approve, pass, and track grants by talking to{" "}
        <strong>@Clew</strong>. This board is the live, read-only view of that
        same pipeline.
      </footer>
    </main>
  );
}
