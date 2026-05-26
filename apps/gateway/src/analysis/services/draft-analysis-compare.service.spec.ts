import { BadRequestException } from '@nestjs/common';
import { SnapshotStore } from '../../drafts/snapshot.store';
import { DraftSnapshot } from '../../drafts/snapshot.types';
import { FastapiClient } from '../../fastapi/fastapi.client';
import { DraftCompareResponse } from '../../fastapi/dto/fastapi-responses';
import { DraftCompareRequestMapper } from '../mappers/draft-compare-request.mapper';
import { AnalysisAnchorPresenter } from '../presenters/analysis-anchor.presenter';
import { CapabilityPresenter } from '../presenters/capability.presenter';
import { DraftComparePresenter } from '../presenters/draft-compare.presenter';
import { InsightPresenter } from '../presenters/insight.presenter';
import { DraftAnalysisCompareService } from './draft-analysis-compare.service';

function snap(hash: string): DraftSnapshot {
  return {
    revisionHash: hash,
    analyzedAt: '2026-01-01T00:00:00.000Z',
    content: `content-${hash}`,
    sections: [],
    analysisStatus: 'fresh',
    capabilities: {} as DraftSnapshot['capabilities'],
  };
}

function upstreamCompare(): DraftCompareResponse {
  const full = { status: 'full' as const, reason_code: null };
  return {
    analysis_id: 'cmp',
    language: 'en',
    title: null,
    previous: {
      revision_hash: 'h-prev',
      analysis: {
        language: 'en',
        title: null,
        capabilities: {} as DraftCompareResponse['previous']['analysis']['capabilities'],
        summary: {
          section_count: 0,
          line_count: 1,
          total_syllables: 1,
          notable_patterns: [],
        },
        insights: [],
        detail: { sections: [] },
      },
    },
    current: {
      revision_hash: 'h-curr',
      analysis: {
        language: 'en',
        title: null,
        capabilities: {} as DraftCompareResponse['current']['analysis']['capabilities'],
        summary: {
          section_count: 0,
          line_count: 1,
          total_syllables: 1,
          notable_patterns: [],
        },
        insights: [],
        detail: { sections: [] },
      },
    },
    summary: {
      motif_delta_count: 0,
      repetition_delta_count: 0,
      section_delta_count: 0,
      consistency_delta_count: 0,
      family_counts: {},
      unmatched_previous_section_ids: [],
      unmatched_current_section_ids: [],
    },
    insights: [],
    capabilities: {
      compare_motifs: full,
      compare_repetition: full,
      compare_sections: full,
      compare_consistency: full,
    },
  };
}

describe('DraftAnalysisCompareService', () => {
  let fastapi: jest.Mocked<FastapiClient>;
  let snapshots: SnapshotStore;
  let service: DraftAnalysisCompareService;

  beforeEach(() => {
    fastapi = {
      analyzeDraftCompare: jest.fn(),
    } as unknown as jest.Mocked<FastapiClient>;
    snapshots = new SnapshotStore();
    service = new DraftAnalysisCompareService(
      fastapi,
      snapshots,
      new DraftCompareRequestMapper(),
      new DraftComparePresenter(
        new CapabilityPresenter(),
        new InsightPresenter(new AnalysisAnchorPresenter()),
      ),
    );
  });

  it('rejects when draftId is missing', async () => {
    await expect(
      service.compareDraft({
        baseRevisionHash: 'h1',
        targetRevisionHash: 'h2',
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('rejects with COMPARE_BASELINE_UNAVAILABLE when base snapshot missing', async () => {
    snapshots.put('d1', snap('h2'));
    try {
      await service.compareDraft({
        draftId: 'd1',
        baseRevisionHash: 'h1',
        targetRevisionHash: 'h2',
      });
      fail('expected BadRequestException');
    } catch (err) {
      expect(err).toBeInstanceOf(BadRequestException);
      const resp = (err as BadRequestException).getResponse() as {
        code: string;
        missing: string;
      };
      expect(resp.code).toBe('COMPARE_BASELINE_UNAVAILABLE');
      expect(resp.missing).toBe('base');
    }
  });

  it('rejects with COMPARE_BASELINE_UNAVAILABLE when target snapshot missing', async () => {
    snapshots.put('d1', snap('h1'));
    try {
      await service.compareDraft({
        draftId: 'd1',
        baseRevisionHash: 'h1',
        targetRevisionHash: 'h2',
      });
      fail('expected BadRequestException');
    } catch (err) {
      const resp = (err as BadRequestException).getResponse() as {
        missing: string;
      };
      expect(resp.missing).toBe('target');
    }
  });

  it('accepts forceRefresh but does not forward it to FastAPI', async () => {
    snapshots.put('d1', snap('h1'));
    snapshots.put('d1', snap('h2'));
    fastapi.analyzeDraftCompare.mockResolvedValue(upstreamCompare());
    await service.compareDraft({
      draftId: 'd1',
      baseRevisionHash: 'h1',
      targetRevisionHash: 'h2',
      forceRefresh: true,
    });
    const callArg = fastapi.analyzeDraftCompare.mock.calls[0][0];
    expect(callArg).not.toHaveProperty('force_refresh');
    expect(callArg).not.toHaveProperty('forceRefresh');
  });

  it('forwards options snake_case to FastAPI and returns a payload', async () => {
    snapshots.put('d1', snap('h1'));
    snapshots.put('d1', snap('h2'));
    fastapi.analyzeDraftCompare.mockResolvedValue(upstreamCompare());
    const out = await service.compareDraft({
      draftId: 'd1',
      baseRevisionHash: 'h1',
      targetRevisionHash: 'h2',
      options: { compareMotifs: true },
    });
    expect(fastapi.analyzeDraftCompare.mock.calls[0][0].options).toEqual({
      compare_motifs: true,
    });
    expect(out.previous.revision_hash).toBe('h-prev');
    expect(out.current.revision_hash).toBe('h-curr');
    expect(out.draft_id).toBe('d1');
  });
});
