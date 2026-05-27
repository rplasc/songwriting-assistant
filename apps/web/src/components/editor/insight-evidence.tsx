"use client";

import { useState } from "react";
import {
  DEFAULT_LANGUAGE,
  type Language,
} from "@/features/language/language-types";
import type { InsightEvidence } from "@/features/draft-analysis/draft-analysis-types";
import {
  EVIDENCE_HIDE_LABEL,
  EVIDENCE_REVEAL_LABEL,
} from "@/features/draft-analysis/insight-copy";

interface InsightEvidenceRevealProps {
  evidence: InsightEvidence | null;
  language?: Language;
}

export function InsightEvidenceReveal({
  evidence,
  language = DEFAULT_LANGUAGE,
}: InsightEvidenceRevealProps) {
  const [open, setOpen] = useState(false);
  if (!evidence) return null;

  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="rounded-sm text-[10px] uppercase tracking-widest text-muted-foreground/70 underline decoration-muted-foreground/30 decoration-dotted underline-offset-[3px] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
      >
        {open ? EVIDENCE_HIDE_LABEL[language] : EVIDENCE_REVEAL_LABEL[language]}
      </button>
      {open && <EvidenceBody evidence={evidence} />}
    </div>
  );
}

function EvidenceBody({ evidence }: { evidence: InsightEvidence }) {
  const { kind, ...rest } = evidence;
  const entries = Object.entries(rest);
  return (
    <dl className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 border-l border-border/60 pl-2.5 text-[11px] leading-relaxed">
      <dt className="text-muted-foreground/70">{kind}</dt>
      <dd className="text-foreground/90" />
      {entries.map(([key, value]) => (
        <EvidenceRow key={key} fieldKey={key} value={value} />
      ))}
    </dl>
  );
}

function EvidenceRow({ fieldKey, value }: { fieldKey: string; value: unknown }) {
  return (
    <>
      <dt className="text-muted-foreground/70">{humanize(fieldKey)}</dt>
      <dd className="wrap-break-word text-foreground/85">{formatValue(value)}</dd>
    </>
  );
}

function humanize(key: string): string {
  // FastAPI evidence keys come back as snake_case. Soften them so the panel
  // reads like notebook annotations rather than a JSON dump.
  return key.replace(/_/g, " ");
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((v) => formatValue(v)).join(", ");
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}
