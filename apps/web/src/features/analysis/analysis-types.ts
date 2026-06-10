import type { Language } from "@/features/language/language-types";
import type { RhymeMode } from "./rhyme-modes";

export interface SyllableToken {
  text: string;
  syllables: number;
  low_confidence?: boolean;
}

export interface RhymeItem {
  word: string;
  syllables: number;
  type: string;
}

export type InnerRhymeType = "perfect" | "near";
export type InnerRhymeConfidence = "high" | "medium" | "low";

/** One rhyming word's position, used by the UI to highlight it. */
export interface InnerRhymeOccurrence {
  lineIndex: number;
  wordIndex: number;
  charStart: number;
  charEnd: number;
  text: string;
  normalized: string;
}

/** A set of words that rhyme with each other, anywhere in the text. */
export interface InnerRhymeGroup {
  id: string;
  rhymeType: InnerRhymeType;
  confidence: InnerRhymeConfidence;
  rhymeKey: string;
  occurrences: InnerRhymeOccurrence[];
}

/** Wire shape (snake_case) emitted by the gateway. */
export interface ServerInnerRhymeOccurrence {
  line_index: number;
  word_index: number;
  char_start: number;
  char_end: number;
  text: string;
  normalized: string;
}

export interface ServerInnerRhymeGroup {
  id: string;
  rhyme_type: InnerRhymeType;
  confidence: InnerRhymeConfidence;
  rhyme_key: string;
  occurrences: ServerInnerRhymeOccurrence[];
}

export interface ServerAnalysisPayload {
  line: string;
  language?: Language;
  syllables: {
    total: number;
    tokens: SyllableToken[];
  };
  rhymes: {
    target_word: string | null;
    mode?: RhymeMode;
    items: RhymeItem[];
  };
  inner_rhymes?: ServerInnerRhymeGroup[];
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

export interface AnalysisResult {
  line: string;
  language: Language;
  totalSyllables: number;
  tokens: SyllableToken[];
  targetWord: string | null;
  rhymes: RhymeItem[];
  innerRhymes: InnerRhymeGroup[];
  rhymeMode: RhymeMode;
  lowConfidence: boolean;
  latencyMs: number;
  requestId?: string;
}

export type AnalysisStatus = "idle" | "loading" | "ready" | "error";
