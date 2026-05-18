import type { RhymeMode } from "./rhyme-modes";

export interface SyllableToken {
  text: string;
  syllables: number;
}

export interface RhymeItem {
  word: string;
  syllables: number;
  type: string;
}

export interface ServerAnalysisPayload {
  line: string;
  syllables: {
    total: number;
    tokens: SyllableToken[];
  };
  rhymes: {
    target_word: string | null;
    mode?: RhymeMode;
    items: RhymeItem[];
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

export interface AnalysisResult {
  line: string;
  totalSyllables: number;
  tokens: SyllableToken[];
  targetWord: string | null;
  rhymes: RhymeItem[];
  rhymeMode: RhymeMode;
  latencyMs: number;
  requestId?: string;
}

export type AnalysisStatus = "idle" | "loading" | "ready" | "error";
