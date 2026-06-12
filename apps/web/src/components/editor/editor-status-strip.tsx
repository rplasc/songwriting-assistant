import type { Language } from "@/features/language/language-types";
import type { RhymeHighlightStyle } from "@/features/settings/preferences";

interface EditorStatusStripProps {
  railOpen: boolean;
  rhymeGroupCount: number;
  rhymeHighlights: boolean;
  rhymeHighlightStyle: RhymeHighlightStyle;
  syllableCounts: boolean;
  offline: boolean;
  language: Language;
}

const COPY: Record<
  Language,
  {
    railOpen: string;
    railClosed: string;
    rhymeGroups: (n: number, style: RhymeHighlightStyle) => string;
    rhymeHighlightsOff: string;
    syllables: string;
    syllablesOff: string;
    offline: string;
  }
> = {
  en: {
    railOpen: "rail open",
    railClosed: "rail closed",
    rhymeGroups: (n, style) => {
      const verb = style === "marker" ? "highlighted" : "underlined";
      return n > 0
        ? `${n} rhyme group${n === 1 ? "" : "s"} ${verb}`
        : `rhyme groups ${verb}`;
    },
    rhymeHighlightsOff: "rhyme highlights off",
    syllables: "syllables at right edge",
    syllablesOff: "syllable counts off",
    offline: "offline",
  },
  es: {
    railOpen: "margen abierto",
    railClosed: "margen cerrado",
    rhymeGroups: (n, style) => {
      const verb = style === "marker" ? "resaltado" : "subrayado";
      const suffix = n === 1 ? "" : "s";
      return n > 0
        ? `${n} grupo${suffix} de rima ${verb}${suffix}`
        : `grupos de rima ${verb}s`;
    },
    rhymeHighlightsOff: "resaltado de rimas desactivado",
    syllables: "sílabas al borde derecho",
    syllablesOff: "conteo de sílabas desactivado",
    offline: "sin conexión",
  },
};

export function EditorStatusStrip({
  railOpen,
  rhymeGroupCount,
  rhymeHighlights,
  rhymeHighlightStyle,
  syllableCounts,
  offline,
  language,
}: EditorStatusStripProps) {
  const copy = COPY[language];
  const segments = [
    railOpen ? copy.railOpen : copy.railClosed,
    rhymeHighlights
      ? copy.rhymeGroups(rhymeGroupCount, rhymeHighlightStyle)
      : copy.rhymeHighlightsOff,
    syllableCounts ? copy.syllables : copy.syllablesOff,
  ];
  if (offline) segments.push(copy.offline);

  return (
    <p className="border-t border-dashed border-border/70 pt-2.5 text-center font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground/70">
      {segments.join(" · ")}
    </p>
  );
}
