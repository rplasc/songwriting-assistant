import { DraftAnalysisPresenter } from './draft-analysis.presenter';
import { DraftAnalysisResponse } from '../../fastapi/dto/fastapi-responses';

function upstream(
  overrides: Partial<DraftAnalysisResponse> = {},
): DraftAnalysisResponse {
  return {
    language: 'en',
    summary: { section_count: 1, line_count: 3 },
    sections: [{ id: 's1', label: 'verse', line_start: 1, line_end: 2 }],
    insights: ['x'],
    capabilities: { rhyme_scheme: true, cadence: true, repetition: true },
    ...overrides,
  };
}

describe('DraftAnalysisPresenter', () => {
  const presenter = new DraftAnalysisPresenter();

  it('emits a snake_case payload with fresh status by default', () => {
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
        summary: { section_count: 1, line_count: 3 },
        sections: [{ id: 's1', label: 'verse', line_start: 1, line_end: 2 }],
        insights: ['x'],
        capabilities: { rhyme_scheme: true, cadence: true, repetition: true },
      },
      meta: { request_id: 'req-1', latency_ms: 12 },
    });
    expect(typeof out.analyzed_at).toBe('string');
  });

  it('sets analysis_status to unsupported when all capabilities are off', () => {
    const out = presenter.toClient({
      draftId: null,
      revisionHash: 'h',
      upstream: upstream({
        capabilities: {
          rhyme_scheme: false,
          cadence: false,
          repetition: false,
        },
      }),
      latencyMs: 1,
    });
    expect(out.analysis_status).toBe('unsupported');
    expect(out.draft_id).toBeNull();
  });
});
