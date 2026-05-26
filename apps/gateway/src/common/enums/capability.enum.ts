export const CAPABILITY_STATUSES = ['full', 'partial', 'unsupported'] as const;
export type CapabilityStatus = (typeof CAPABILITY_STATUSES)[number];

export const CAPABILITY_REASON_CODES = [
  'language_unsupported',
  'model_unavailable',
  'insufficient_lines',
  'option_not_requested',
  'language_partial_support',
] as const;
export type CapabilityReasonCode = (typeof CAPABILITY_REASON_CODES)[number];

export const INSIGHT_SEVERITIES = ['info', 'low', 'medium', 'high'] as const;
export type InsightSeverity = (typeof INSIGHT_SEVERITIES)[number];

export const INSIGHT_CONFIDENCES = ['low', 'medium', 'high'] as const;
export type InsightConfidence = (typeof INSIGHT_CONFIDENCES)[number];

export const ANCHOR_SCOPES = ['draft', 'section'] as const;
export type AnchorScope = (typeof ANCHOR_SCOPES)[number];

export const CAPABILITY_KEYS = [
  'rhyme_scheme',
  'cadence_patterns',
  'stress_hints',
  'repetition',
  'mixed_language',
  'semantic_repetition',
  'motif_tracking',
  'section_contrast',
  'consistency_hints',
] as const;
export type CapabilityKey = (typeof CAPABILITY_KEYS)[number];
