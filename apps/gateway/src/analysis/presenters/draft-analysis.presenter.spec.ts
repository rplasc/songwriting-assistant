import { AnalysisAnchorPresenter } from './analysis-anchor.presenter';
import { CapabilityPresenter } from './capability.presenter';
import { DraftAnalysisPresenter } from './draft-analysis.presenter';
import { InsightPresenter } from './insight.presenter';
import {
  DraftAnalysisCapabilities,
  DraftAnalysisResponse,
} from '../../fastapi/dto/fastapi-responses';

function caps(
  overrides: Partial<DraftAnalysisCapabilities> = {},
): DraftAnalysisCapabilities {
  const cap = (s: 'full' | 'partial' | 'unsupported') => ({
    status: s,
    reason_code: s === 'unsupported' ? 'language_unsupported' : null,
  });
  return {
    rhyme_scheme: cap('full'),
    cadence_patterns: cap('full'),
    stress_hints: cap('unsupported'),
    repetition: cap('full'),
    mixed_language: cap('unsupported'),
    semantic_repetition: cap('unsupported'),
    motif_tracking: cap('unsupported'),
    section_contrast: cap('unsupported'),
    consistency_hints: cap('unsupported'),
    ...overrides,
  };
}

function upstream(
  overrides: Partial<DraftAnalysisResponse> = {},
): DraftAnalysisResponse {
  return {
    language: 'en',
    title: 'My Draft',
    summary: {
      section_count: 1,
      line_count: 3,
      total_syllables: 12,
      notable_patterns: ['ABAB'],
    },
    detail: {
      sections: [
        {
          id: 's1',
          label: 'verse',
          line_start: 1,
          line_end: 2,
          line_count: 2,
          rhyme_scheme: 'AB',
          rhyme_scheme_confidence: 'full',
          syllable_pattern: [8, 8],
          syllable_variance: 0,
          cadence_class: 'consistent',
          repetition_signals: [],
        },
      ],
    },
    insights: [
      {
        id: 'i1',
        type: 'syllable_variance',
        scope: 'section',
        target: 's1',
        severity: 'low',
        message: 'mild variance',
        evidence: { kind: 'syllable_variance', variance: 0.1 },
        anchor: {
          scope: 'section',
          section_id: 's1',
          line_start: 1,
          line_end: 2,
        },
        confidence: 'high',
        hook_context: false,
      },
    ],
    capabilities: caps(),
    ...overrides,
  };
}

function buildPresenter(): DraftAnalysisPresenter {
  return new DraftAnalysisPresenter(
    new CapabilityPresenter(),
    new InsightPresenter(new AnalysisAnchorPresenter()),
  );
}

describe('DraftAnalysisPresenter', () => {
  const presenter = buildPresenter();

  it('emits payload with fresh status, detail.sections, and typed insights', () => {
    const out = presenter.toClient({
      draftId: 'd1',
      revisionHash: 'abc1234567890def',
      upstream: upstream(),
      latencyMs: 12.4,
      requestId: 'req-1',
    });
    expect(out.draft_id).toBe('d1');
    expect(out.revision_hash).toBe('abc1234567890def');
    expect(out.analysis_status).toBe('fresh');
    expect(out.analysis.detail.sections[0]).toMatchObject({
      id: 's1',
      label: 'verse',
      rhyme_scheme: 'AB',
      cadence_class: 'consistent',
    });
    expect(out.analysis.insights[0]).toMatchObject({
      id: 'i1',
      type: 'syllable_variance',
      severity: 'low',
      evidence: { kind: 'syllable_variance', variance: 0.1 },
      anchor: { scope: 'section', section_id: 's1', line_start: 1, line_end: 2 },
      confidence: 'high',
      hook_context: false,
    });
    expect(out.analysis.capabilities.rhyme_scheme).toEqual({
      status: 'full',
      reason_code: null,
    });
    expect(out.analysis.capabilities.semantic_repetition).toEqual({
      status: 'unsupported',
      reason_code: 'language_unsupported',
    });
    expect(out.meta).toEqual({ request_id: 'req-1', latency_ms: 12 });
    expect(typeof out.analyzed_at).toBe('string');
  });

  it('sets analysis_status to unsupported when all capabilities are unsupported', () => {
    const allUnsupported = caps({
      rhyme_scheme: { status: 'unsupported', reason_code: 'language_unsupported' },
      cadence_patterns: { status: 'unsupported', reason_code: 'language_unsupported' },
      repetition: { status: 'unsupported', reason_code: 'language_unsupported' },
    });
    const out = presenter.toClient({
      draftId: null,
      revisionHash: 'h',
      upstream: upstream({ capabilities: allUnsupported }),
      latencyMs: 1,
    });
    expect(out.analysis_status).toBe('unsupported');
    expect(out.draft_id).toBeNull();
  });

  it('treats partial capability as fresh', () => {
    const partial = caps({
      rhyme_scheme: { status: 'partial', reason_code: 'insufficient_lines' },
      cadence_patterns: { status: 'unsupported', reason_code: 'language_unsupported' },
      repetition: { status: 'unsupported', reason_code: 'language_unsupported' },
    });
    const out = presenter.toClient({
      draftId: null,
      revisionHash: 'h',
      upstream: upstream({ capabilities: partial }),
      latencyMs: 1,
    });
    expect(out.analysis_status).toBe('fresh');
  });
});
