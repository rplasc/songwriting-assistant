import type { Language } from "@/features/language/language-types";

interface EditorStatusStripProps {
  railOpen: boolean;
  rhymeGroupCount: number;
  rhymeHighlights: boolean;
  offline: boolean;
  language: Language;
}

const COPY: Record<
  Language,
  {
    railOpen: string;
    railClosed: string;
    rhymeGroups: (n: number) => string;
    rhymeHighlightsOff: string;
    syllables: string;
    offline: string;
  }
> = {
  en: {
    railOpen: "rail open",
    railClosed: "rail closed",
    rhymeGroups: (n) =>
      n > 0 ? `${n} rhyme group${n === 1 ? "" : "s"} underlined` : "rhyme groups underlined",
    rhymeHighlightsOff: "rhyme highlights off",
    syllables: "syllables at right edge",
    offline: "offline",
  },
  es: {
    railOpen: "margen abierto",
    railClosed: "margen cerrado",
    rhymeGroups: (n) =>
      n > 0 ? `${n} grupo${n === 1 ? "" : "s"} de rima subrayado${n === 1 ? "" : "s"}` : "grupos de rima subrayados",
    rhymeHighlightsOff: "resaltado de rimas desactivado",
    syllables: "sílabas al borde derecho",
    offline: "sin conexión",
  },
};

export function EditorStatusStrip({
  railOpen,
  rhymeGroupCount,
  rhymeHighlights,
  offline,
  language,
}: EditorStatusStripProps) {
  const copy = COPY[language];
  const segments = [
    railOpen ? copy.railOpen : copy.railClosed,
    rhymeHighlights ? copy.rhymeGroups(rhymeGroupCount) : copy.rhymeHighlightsOff,
    copy.syllables,
  ];
  if (offline) segments.push(copy.offline);

  return (
    <p className="border-t border-dashed border-border/70 pt-2.5 text-center font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground/70">
      {segments.join(" · ")}
    </p>
  );
}
