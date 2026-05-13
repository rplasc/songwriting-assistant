export interface AnalyzeLineRequest {
  line: string;
}

export interface RhymesRequest {
  word: string;
  limit?: number;
  include_near?: boolean;
}
