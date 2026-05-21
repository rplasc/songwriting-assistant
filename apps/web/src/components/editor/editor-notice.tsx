"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type NoticeTone = "alert" | "warn" | "info";

const TONE: Record<NoticeTone, { border: string; lead: string }> = {
  alert: { border: "border-l-danger/85", lead: "text-danger" },
  warn: { border: "border-l-warn/85", lead: "text-warn" },
  info: { border: "border-l-accent/80", lead: "text-accent" },
};

interface EditorNoticeProps {
  tone: NoticeTone;
  /** Short imperative phrase, set in the accent color — like a margin lede. */
  lead: string;
  /** Conversational follow-up in muted ink. */
  children: ReactNode;
  actions?: ReactNode;
}

export function EditorNotice({
  tone,
  lead,
  children,
  actions,
}: EditorNoticeProps) {
  const t = TONE[tone];
  return (
    <aside
      role="status"
      aria-live="polite"
      className={cn(
        "flex flex-wrap items-baseline gap-x-3 gap-y-1 border-l-2 bg-surface/60 px-3 py-2",
        "text-[12px] leading-snug",
        "motion-safe:animate-[notice-in_220ms_cubic-bezier(0.22,1,0.36,1)]",
        t.border,
      )}
    >
      <span className={cn("font-medium tracking-tight", t.lead)}>{lead}</span>
      <span className="min-w-0 flex-1 text-muted-foreground">{children}</span>
      {actions ? (
        <span className="ml-auto flex shrink-0 items-baseline gap-3 text-[11px]">
          {actions}
        </span>
      ) : null}
    </aside>
  );
}

interface NoticeActionProps {
  onClick: () => void;
  children: ReactNode;
  emphasis?: "default" | "subtle";
}

export function NoticeAction({
  onClick,
  children,
  emphasis = "default",
}: NoticeActionProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center underline decoration-dotted decoration-1 underline-offset-[3px]",
        "transition-colors duration-150 ease-out",
        "focus-visible:outline-none focus-visible:text-accent",
        emphasis === "subtle"
          ? "text-muted-foreground hover:text-foreground"
          : "text-foreground hover:text-accent",
      )}
    >
      {children}
    </button>
  );
}
