export const SUPPORTED_ANALYSIS_MODES = ['standard', 'revision_review'] as const;
export type AnalysisMode = (typeof SUPPORTED_ANALYSIS_MODES)[number];

export const DEFAULT_ANALYSIS_MODE: AnalysisMode = 'standard';
