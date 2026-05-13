export interface TokenAnalysis {
  text: string;
  normalized: string;
  syllables: number;
  pronunciation_found: boolean;
}

export interface LastWord {
  text: string;
  normalized: string;
  pronunciation_found: boolean;
}

export interface LineAnalysisResponse {
  line: string;
  normalized_line: string;
  total_syllables: number;
  tokens: TokenAnalysis[];
  last_word: LastWord | null;
}

export interface RhymeCandidate {
  word: string;
  syllables: number;
  rhyme_type: string;
  score: number;
}

export interface RhymeMeta {
  limit: number;
  include_near: boolean;
}

export interface RhymeResponse {
  word: string;
  normalized_word: string | null;
  pronunciations_found: boolean;
  rhymes: RhymeCandidate[];
  meta: RhymeMeta;
}
