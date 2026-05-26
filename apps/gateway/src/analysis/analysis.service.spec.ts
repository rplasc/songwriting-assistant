import { AnalysisService } from './analysis.service';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import { AnalysisAnchorPresenter } from './presenters/analysis-anchor.presenter';
import { CapabilityPresenter } from './presenters/capability.presenter';
import { DraftAnalysisPresenter } from './presenters/draft-analysis.presenter';
import { InsightPresenter } from './presenters/insight.presenter';
import { DraftsService } from '../drafts/drafts.service';
import { SnapshotStore } from '../drafts/snapshot.store';
import { FastapiClient } from '../fastapi/fastapi.client';
import {
  DraftAnalysisCapabilities,
  DraftAnalysisResponse,
} from '../fastapi/dto/fastapi-responses';

function caps(
  overrides: Partial<DraftAnalysisCapabilities> = {},
): DraftAnalysisCapabilities {
  const cap = (status: 'full' | 'partial' | 'unsupported') => ({
    status,
    reason_code: status === 'unsupported' ? 'language_unsupported' : null,
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

function upstreamFixture(
  overrides: Partial<DraftAnalysisResponse> = {},
): DraftAnalysisResponse {
  return {
    language: 'en',
    title: null,
    summary: {
      section_count: 0,
      line_count: 2,
      total_syllables: 10,
      notable_patterns: [],
    },
    detail: { sections: [] },
    insights: [],
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

describe('AnalysisService', () => {
  let fastapi: jest.Mocked<FastapiClient>;
  let drafts: jest.Mocked<DraftsService>;
  let snapshots: SnapshotStore;
  let service: AnalysisService;

  beforeEach(() => {
    fastapi = {
      analyzeDraft: jest.fn(),
    } as unknown as jest.Mocked<FastapiClient>;
    drafts = {
      findById: jest.fn(),
      recordAnalysis: jest.fn(),
    } as unknown as jest.Mocked<DraftsService>;
    snapshots = new SnapshotStore();
    service = new AnalysisService(
      fastapi,
      drafts,
      snapshots,
      new DraftAnalysisRequestMapper(),
      buildPresenter(),
    );
  });

  it('forwards inline sections to FastAPI when provided', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({
      content: 'a\nb',
      inlineSections: [{ label: 'verse', lineStart: 1, lineEnd: 2 }],
    });
    expect(drafts.findById).not.toHaveBeenCalled();
    const callArg = fastapi.analyzeDraft.mock.calls[0][0];
    expect(callArg.sections).toHaveLength(1);
    expect(callArg.sections?.[0]).toMatchObject({
      label: 'verse',
      line_start: 1,
      line_end: 2,
    });
  });

  it('falls back to stored draft sections when no inline sections supplied', async () => {
    drafts.findById.mockReturnValue({
      id: 'd1',
      title: 't',
      content: 'a\nb',
      language: 'en',
      sections: [
        { id: 'sec-x', label: 'chorus', lineStart: 1, lineEnd: 2 },
      ],
      version: 1,
      createdAt: 'x',
      updatedAt: 'x',
    });
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({ draftId: 'd1', content: 'a\nb' });
    expect(drafts.findById).toHaveBeenCalledWith('d1');
    const callArg = fastapi.analyzeDraft.mock.calls[0][0];
    expect(callArg.sections?.[0].id).toBe('sec-x');
    expect(callArg.sections?.[0].label).toBe('chorus');
  });

  it('sends sections as undefined when no draft id and no inline sections', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({ content: 'a\nb' });
    expect(fastapi.analyzeDraft.mock.calls[0][0].sections).toBeUndefined();
  });

  it('computes a deterministic revisionHash from content', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    const a = await service.analyzeDraft({ content: 'same content' });
    const b = await service.analyzeDraft({ content: 'same content' });
    expect(a.revision_hash).toBe(b.revision_hash);
    expect(a.revision_hash).toHaveLength(16);
  });

  it('populates meta.latency_ms and meta.request_id', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    const out = await service.analyzeDraft({
      content: 'x',
      requestId: 'req-123',
    });
    expect(out.meta.request_id).toBe('req-123');
    expect(typeof out.meta.latency_ms).toBe('number');
    expect(out.meta.latency_ms).toBeGreaterThanOrEqual(0);
  });

  it('marks analysis_status unsupported when all capabilities are unsupported', async () => {
    fastapi.analyzeDraft.mockResolvedValue(
      upstreamFixture({
        capabilities: caps({
          rhyme_scheme: { status: 'unsupported', reason_code: 'language_unsupported' },
          cadence_patterns: { status: 'unsupported', reason_code: 'language_unsupported' },
          repetition: { status: 'unsupported', reason_code: 'language_unsupported' },
        }),
      }),
    );
    const out = await service.analyzeDraft({ content: 'x' });
    expect(out.analysis_status).toBe('unsupported');
  });

  it('marks analysis_status fresh when at least one capability is not unsupported', async () => {
    fastapi.analyzeDraft.mockResolvedValue(
      upstreamFixture({
        capabilities: caps({
          rhyme_scheme: { status: 'unsupported', reason_code: 'language_unsupported' },
          cadence_patterns: { status: 'unsupported', reason_code: 'language_unsupported' },
          repetition: { status: 'partial', reason_code: 'insufficient_lines' },
        }),
      }),
    );
    const out = await service.analyzeDraft({ content: 'x' });
    expect(out.analysis_status).toBe('fresh');
  });

  it('passes title to FastAPI', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture({ title: 'My Song' }));
    const out = await service.analyzeDraft({
      content: 'x',
      title: 'My Song',
    });
    expect(fastapi.analyzeDraft.mock.calls[0][0].title).toBe('My Song');
    expect(out.analysis.title).toBe('My Song');
  });

  it('does not forward force_refresh or revision_hash to FastAPI', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({ content: 'x', forceRefresh: true });
    const callArg = fastapi.analyzeDraft.mock.calls[0][0];
    expect(callArg).not.toHaveProperty('force_refresh');
    expect(callArg).not.toHaveProperty('revision_hash');
  });

  it('forwards options in snake_case when analysisMode is revision_review', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({
      content: 'x',
      analysisMode: 'revision_review',
      options: {
        includeSemanticRepetition: true,
        includeMotifTracking: false,
      },
    });
    const callArg = fastapi.analyzeDraft.mock.calls[0][0];
    expect(callArg.options).toEqual({
      include_semantic_repetition: true,
      include_motif_tracking: false,
    });
  });

  it('drops options when analysisMode is standard (default)', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({
      content: 'x',
      options: { includeSemanticRepetition: true },
    });
    expect(fastapi.analyzeDraft.mock.calls[0][0].options).toBeUndefined();
  });

  it('writes a snapshot and records analysis provenance when draftId is present', async () => {
    drafts.findById.mockReturnValue({
      id: 'd1',
      title: 't',
      content: 'lyrics',
      language: 'en',
      version: 1,
      createdAt: 'x',
      updatedAt: 'x',
    });
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    const out = await service.analyzeDraft({
      draftId: 'd1',
      content: 'lyrics',
    });
    expect(drafts.recordAnalysis).toHaveBeenCalledWith('d1', {
      lastAnalyzedAt: out.analyzed_at,
      lastAnalysisStatus: out.analysis_status,
      latestAnalyzedRevisionHash: out.revision_hash,
    });
    expect(snapshots.find('d1', out.revision_hash)).not.toBeNull();
  });

  it('does not write snapshots or provenance for anonymous (no draftId) analyses', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    const out = await service.analyzeDraft({ content: 'lyrics' });
    expect(drafts.recordAnalysis).not.toHaveBeenCalled();
    // SnapshotStore is keyed by draftId; with none provided, nothing stored.
    expect(snapshots.find('', out.revision_hash)).toBeNull();
  });
});
