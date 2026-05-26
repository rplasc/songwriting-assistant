import { CapabilityPresenter } from './capability.presenter';
import { DraftAnalysisCapabilities } from '../../fastapi/dto/fastapi-responses';

function buildCaps(): DraftAnalysisCapabilities {
  const cap = (s: 'full' | 'partial' | 'unsupported') => ({
    status: s,
    reason_code: s === 'unsupported' ? 'language_unsupported' : null,
  });
  return {
    rhyme_scheme: cap('full'),
    cadence_patterns: cap('partial'),
    stress_hints: cap('unsupported'),
    repetition: cap('full'),
    mixed_language: cap('unsupported'),
    semantic_repetition: cap('unsupported'),
    motif_tracking: cap('unsupported'),
    section_contrast: cap('unsupported'),
    consistency_hints: cap('unsupported'),
  };
}

describe('CapabilityPresenter', () => {
  const presenter = new CapabilityPresenter();

  it('maps every capability key through', () => {
    const out = presenter.toClient(buildCaps());
    expect(out.rhyme_scheme).toEqual({ status: 'full', reason_code: null });
    expect(out.cadence_patterns).toEqual({ status: 'partial', reason_code: null });
    expect(out.semantic_repetition).toEqual({
      status: 'unsupported',
      reason_code: 'language_unsupported',
    });
  });

  it('anyEnabled returns true when any capability is non-unsupported', () => {
    expect(presenter.anyEnabled(buildCaps())).toBe(true);
  });

  it('anyEnabled returns false when all unsupported', () => {
    const cap = { status: 'unsupported' as const, reason_code: 'language_unsupported' as const };
    const allUnsupported: DraftAnalysisCapabilities = {
      rhyme_scheme: cap,
      cadence_patterns: cap,
      stress_hints: cap,
      repetition: cap,
      mixed_language: cap,
      semantic_repetition: cap,
      motif_tracking: cap,
      section_contrast: cap,
      consistency_hints: cap,
    };
    expect(presenter.anyEnabled(allUnsupported)).toBe(false);
  });
});
