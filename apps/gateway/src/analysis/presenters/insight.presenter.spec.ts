import { AnalysisAnchorPresenter } from './analysis-anchor.presenter';
import { InsightPresenter } from './insight.presenter';
import { UpstreamInsight } from '../../fastapi/dto/fastapi-responses';

function insight(overrides: Partial<UpstreamInsight> = {}): UpstreamInsight {
  return {
    id: 'i1',
    type: 'syllable_variance',
    scope: 'section',
    target: 's1',
    severity: 'low',
    message: 'msg',
    evidence: { kind: 'syllable_variance', variance: 0.3 },
    anchor: {
      scope: 'section',
      section_id: 's1',
      line_start: 1,
      line_end: 2,
    },
    confidence: 'medium',
    hook_context: false,
    ...overrides,
  };
}

describe('InsightPresenter', () => {
  const presenter = new InsightPresenter(new AnalysisAnchorPresenter());

  it('maps a single insight passing evidence kind through', () => {
    const out = presenter.toClient(insight());
    expect(out).toEqual({
      id: 'i1',
      type: 'syllable_variance',
      scope: 'section',
      target: 's1',
      severity: 'low',
      message: 'msg',
      evidence: { kind: 'syllable_variance', variance: 0.3 },
      anchor: {
        scope: 'section',
        section_id: 's1',
        line_start: 1,
        line_end: 2,
      },
      confidence: 'medium',
      hook_context: false,
    });
  });

  it('handles null evidence and anchor', () => {
    const out = presenter.toClient(
      insight({ evidence: null, anchor: null, confidence: null }),
    );
    expect(out.evidence).toBeNull();
    expect(out.anchor).toBeNull();
    expect(out.confidence).toBeNull();
  });

  it('toClientList maps every entry', () => {
    const out = presenter.toClientList([
      insight({ id: 'a' }),
      insight({ id: 'b' }),
    ]);
    expect(out.map((i) => i.id)).toEqual(['a', 'b']);
  });
});
