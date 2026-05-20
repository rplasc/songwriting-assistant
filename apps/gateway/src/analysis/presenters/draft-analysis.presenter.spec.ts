import { DraftAnalysisPresenter } from './draft-analysis.presenter';
import { DraftAnalysisResponse } from '../../fastapi/dto/fastapi-responses';

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
    sections: [
      {
        id: 's1',
        label: 'verse',
        line_start: 1,
        line_end: 2,
        line_count: 2,
        rhyme_scheme: 'AB',
        rhyme_scheme_confidence: 0.9,
        syllable_pattern: [8, 8],
        syllable_variance: 0,
        cadence_class: 'consistent',
        repetition_signals: [],
      },
    ],
    insights: ['x'],
    capabilities: {
      rhyme_scheme: 'full',
      cadence_patterns: 'full',
      stress_hints: 'unsupported',
      repetition: 'full',
      mixed_language: 'unsupported',
    },
    ...overrides,
  };
}

describe('DraftAnalysisPresenter', () => {
  const presenter = new DraftAnalysisPresenter();

  it('emits payload with fresh status when capabilities present', () => {
    const out = presenter.toClient({
      draftId: 'd1',
      revisionHash: 'abc1234567890def',
      upstream: upstream(),
      latencyMs: 12.4,
      requestId: 'req-1',
    });
    expect(out).toMatchObject({
      draft_id: 'd1',
      revision_hash: 'abc1234567890def',
      analysis_status: 'fresh',
      analysis: {
        language: 'en',
        title: 'My Draft',
        summary: {
          section_count: 1,
          line_count: 3,
          total_syllables: 12,
          notable_patterns: ['ABAB'],
        },
        sections: [
          expect.objectContaining({
            id: 's1',
            label: 'verse',
            rhyme_scheme: 'AB',
            cadence_class: 'consistent',
          }),
        ],
        insights: ['x'],
        capabilities: {
          rhyme_scheme: 'full',
          cadence_patterns: 'full',
          stress_hints: 'unsupported',
          repetition: 'full',
          mixed_language: 'unsupported',
        },
      },
      meta: { request_id: 'req-1', latency_ms: 12 },
    });
    expect(typeof out.analyzed_at).toBe('string');
  });

  it('sets analysis_status to unsupported when all capabilities are unsupported', () => {
    const out = presenter.toClient({
      draftId: null,
      revisionHash: 'h',
      upstream: upstream({
        capabilities: {
          rhyme_scheme: 'unsupported',
          cadence_patterns: 'unsupported',
          stress_hints: 'unsupported',
          repetition: 'unsupported',
          mixed_language: 'unsupported',
        },
      }),
      latencyMs: 1,
    });
    expect(out.analysis_status).toBe('unsupported');
    expect(out.draft_id).toBeNull();
  });

  it('treats partial capability as fresh', () => {
    const out = presenter.toClient({
      draftId: null,
      revisionHash: 'h',
      upstream: upstream({
        capabilities: {
          rhyme_scheme: 'partial',
          cadence_patterns: 'unsupported',
          stress_hints: 'unsupported',
          repetition: 'unsupported',
          mixed_language: 'unsupported',
        },
      }),
      latencyMs: 1,
    });
    expect(out.analysis_status).toBe('fresh');
  });
});
