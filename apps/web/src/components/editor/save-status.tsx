"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { SaveStatus } from "@/features/drafts/drafts-types";

interface SaveStatusProps {
  status: SaveStatus;
  lastSavedAt: Date | null;
}

function formatRelative(target: Date, now: Date): string {
  const seconds = Math.max(0, Math.round((now.getTime() - target.getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

const DOT_CLASS: Record<SaveStatus, string> = {
  idle: "bg-muted-foreground/35",
  dirty: "bg-warn/80",
  saving: "bg-accent/80 animate-pulse",
  saved: "bg-success/85",
  offline: "bg-danger/85",
};

export function SaveStatusIndicator({ status, lastSavedAt }: SaveStatusProps) {
  // Tick once a second so "Saved Ns ago" stays fresh.
  const [, setTick] = useState(0);
  useEffect(() => {
    if (status !== "saved") return;
    const interval = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(interval);
  }, [status]);

  // Stay quiet on an empty page — a co-writer wouldn't narrate a blank slate.
  if (status === "idle") return null;

  let label: string;
  switch (status) {
    case "dirty":
      label = "Unsaved";
      break;
    case "saving":
      label = "Saving…";
      break;
    case "saved":
      label = lastSavedAt
        ? `Saved ${formatRelative(lastSavedAt, new Date())}`
        : "Saved";
      break;
    case "offline":
      label = "Offline — retrying";
      break;
  }

  return (
    <span
      role="status"
      aria-live="polite"
      className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground tabular-nums"
    >
      <span
        aria-hidden
        className={cn("inline-block h-1 w-1 rounded-full", DOT_CLASS[status])}
      />
      {label}
    </span>
  );
}
