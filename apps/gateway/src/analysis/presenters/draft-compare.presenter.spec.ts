import {
  DraftAnalysisCapabilities,
  DraftCompareResponse,
  DraftRevisionUpstream,
} from '../../fastapi/dto/fastapi-responses';
import { AnalysisAnchorPresenter } from './analysis-anchor.presenter';
import { CapabilityPresenter } from './capability.presenter';
import { DraftComparePresenter } from './draft-compare.presenter';
import { InsightPresenter } from './insight.presenter';

function caps(): DraftAnalysisCapabilities {
  const full = { status: 'full' as const, reason_code: null };
  const off = { status: 'unsupported' as const, reason_code: 'language_unsupported' as const };
  return {
    rhyme_scheme: full,
    cadence_patterns: full,
    stress_hints: off,
    repetition: full,
    mixed_language: off,
    semantic_repetition: off,
    motif_tracking: off,
    section_contrast: off,
    consistency_hints: off,
  };
}

function revision(hash: string): DraftRevisionUpstream {
  return {
    revision_hash: hash,
    analysis: {
      language: 'en',
      title: null,
      capabilities: caps(),
      summary: {
        section_count: 0,
        line_count: 1,
        total_syllables: 5,
        notable_patterns: [],
      },
      insights: [],
      detail: { sections: [] },
    },
  };
}

function upstream(): DraftCompareResponse {
  return {
    analysis_id: 'cmp-1',
    language: 'en',
    title: null,
    previous: revision('h-prev'),
    current: revision('h-curr'),
    summary: {
      motif_delta_count: 1,
      repetition_delta_count: 0,
      section_delta_count: 2,
      consistency_delta_count: 0,
      family_counts: { motif: 1, section: 2 },
      unmatched_previous_section_ids: ['p1'],
      unmatched_current_section_ids: [],
    },
    insights: [
      {
        id: 'i1',
        type: 'motif_added',
        scope: 'draft',
        target: null,
        severity: 'info',
        message: 'new motif',
        evidence: { kind: 'motif_added', motif: 'window' },
        anchor: null,
        confidence: 'medium',
        hook_context: false,
      },
    ],
    capabilities: {
      compare_motifs: { status: 'full', reason_code: null },
      compare_repetition: { status: 'full', reason_code: null },
      compare_sections: { status: 'partial', reason_code: 'insufficient_lines' },
      compare_consistency: { status: 'unsupported', reason_code: 'option_not_requested' },
    },
  };
}

describe('DraftComparePresenter', () => {
  const presenter = new DraftComparePresenter(
    new CapabilityPresenter(),
    new InsightPresenter(new AnalysisAnchorPresenter()),
  );

  it('maps upstream compare response to client payload', () => {
    const out = presenter.toClient({
      upstream: upstream(),
      draftId: 'd1',
      latencyMs: 22.6,
      requestId: 'req-1',
    });
    expect(out.analysis_id).toBe('cmp-1');
    expect(out.draft_id).toBe('d1');
    expect(out.previous.revision_hash).toBe('h-prev');
    expect(out.current.revision_hash).toBe('h-curr');
    expect(out.summary.motif_delta_count).toBe(1);
    expect(out.summary.unmatched_previous_section_ids).toEqual(['p1']);
    expect(out.insights[0]).toMatchObject({
      id: 'i1',
      type: 'motif_added',
      evidence: { kind: 'motif_added', motif: 'window' },
    });
    expect(out.capabilities.compare_motifs).toEqual({
      status: 'full',
      reason_code: null,
    });
    expect(out.capabilities.compare_sections).toEqual({
      status: 'partial',
      reason_code: 'insufficient_lines',
    });
    expect(out.meta).toEqual({ request_id: 'req-1', latency_ms: 23 });
  });
});
