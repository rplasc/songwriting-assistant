import { AnalysisService } from './analysis.service';
import { DraftAnalysisRequestMapper } from './mappers/draft-analysis-request.mapper';
import { DraftAnalysisPresenter } from './presenters/draft-analysis.presenter';
import { DraftsService } from '../drafts/drafts.service';
import { FastapiClient } from '../fastapi/fastapi.client';
import { DraftAnalysisResponse } from '../fastapi/dto/fastapi-responses';

function upstreamFixture(
  overrides: Partial<DraftAnalysisResponse> = {},
): DraftAnalysisResponse {
  return {
    language: 'en',
    summary: { section_count: 0, line_count: 2 },
    sections: [],
    insights: [],
    capabilities: { rhyme_scheme: true, cadence: true, repetition: true },
    ...overrides,
  };
}

describe('AnalysisService', () => {
  let fastapi: jest.Mocked<FastapiClient>;
  let drafts: jest.Mocked<DraftsService>;
  let service: AnalysisService;

  beforeEach(() => {
    fastapi = {
      analyzeDraft: jest.fn(),
    } as unknown as jest.Mocked<FastapiClient>;
    drafts = {
      findById: jest.fn(),
    } as unknown as jest.Mocked<DraftsService>;
    service = new AnalysisService(
      fastapi,
      drafts,
      new DraftAnalysisRequestMapper(),
      new DraftAnalysisPresenter(),
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

  it('sends empty sections when no draft id and no inline sections', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({ content: 'a\nb' });
    expect(fastapi.analyzeDraft.mock.calls[0][0].sections).toEqual([]);
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

  it('marks analysis_status unsupported when all capabilities are off', async () => {
    fastapi.analyzeDraft.mockResolvedValue(
      upstreamFixture({
        capabilities: {
          rhyme_scheme: false,
          cadence: false,
          repetition: false,
        },
      }),
    );
    const out = await service.analyzeDraft({ content: 'x' });
    expect(out.analysis_status).toBe('unsupported');
  });

  it('marks analysis_status fresh when at least one capability is enabled', async () => {
    fastapi.analyzeDraft.mockResolvedValue(
      upstreamFixture({
        capabilities: {
          rhyme_scheme: false,
          cadence: false,
          repetition: true,
        },
      }),
    );
    const out = await service.analyzeDraft({ content: 'x' });
    expect(out.analysis_status).toBe('fresh');
  });

  it('forwards forceRefresh flag and revision_hash to FastAPI', async () => {
    fastapi.analyzeDraft.mockResolvedValue(upstreamFixture());
    await service.analyzeDraft({ content: 'x', forceRefresh: true });
    const callArg = fastapi.analyzeDraft.mock.calls[0][0];
    expect(callArg.force_refresh).toBe(true);
    expect(callArg.revision_hash).toHaveLength(16);
  });
});
