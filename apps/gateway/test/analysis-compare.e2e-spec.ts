import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/app.module';
import { HttpExceptionFilter } from '../src/common/filters/http-exception.filter';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Analyze Draft Compare (e2e)', () => {
  let app: INestApplication<App>;
  const fullCap = { status: 'full' as const, reason_code: null };
  const offCap = {
    status: 'unsupported' as const,
    reason_code: 'language_unsupported' as const,
  };

  const analysisCapabilities = {
    rhyme_scheme: fullCap,
    cadence_patterns: fullCap,
    stress_hints: offCap,
    repetition: fullCap,
    mixed_language: offCap,
    semantic_repetition: offCap,
    motif_tracking: offCap,
    section_contrast: offCap,
    consistency_hints: offCap,
  };

  const analyzeDraftFixture = {
    language: 'en',
    title: null,
    capabilities: analysisCapabilities,
    summary: {
      section_count: 0,
      line_count: 1,
      total_syllables: 4,
      notable_patterns: [],
    },
    insights: [],
    detail: { sections: [] },
  };

  const fastapiMock = {
    ping: jest.fn().mockResolvedValue(true),
    analyzeLine: jest.fn(),
    getRhymes: jest.fn(),
    analyzeDraft: jest.fn(),
    analyzeDraftCompare: jest.fn(),
  };

  beforeAll(async () => {
    process.env.FASTAPI_BASE_URL = 'http://localhost:9999';
    const mod = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(FastapiClient)
      .useValue(fastapiMock)
      .compile();
    app = mod.createNestApplication();
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        transform: true,
        forbidNonWhitelisted: true,
      }),
    );
    app.useGlobalFilters(new HttpExceptionFilter());
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  beforeEach(() => {
    fastapiMock.analyzeDraft.mockReset();
    fastapiMock.analyzeDraftCompare.mockReset();
  });

  async function createDraft(content: string): Promise<string> {
    const res = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content, title: 't' });
    expect(res.status).toBe(201);
    return res.body.data.id as string;
  }

  async function analyze(draftId: string, content: string): Promise<string> {
    fastapiMock.analyzeDraft.mockResolvedValueOnce(analyzeDraftFixture);
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft')
      .send({ draftId, content });
    expect(res.status).toBe(201);
    return res.body.revision_hash as string;
  }

  it('returns 400 when draftId is missing', async () => {
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft-compare')
      .send({ baseRevisionHash: 'a', targetRevisionHash: 'b' });
    expect(res.status).toBe(400);
    expect(res.body.error?.code).toBe('COMPARE_REQUIRES_DRAFT_ID');
  });

  it('returns 400 COMPARE_BASELINE_UNAVAILABLE when no snapshots exist', async () => {
    const draftId = await createDraft('lyrics');
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft-compare')
      .send({ draftId, baseRevisionHash: 'a', targetRevisionHash: 'b' });
    expect(res.status).toBe(400);
    expect(res.body.error?.code).toBe('COMPARE_BASELINE_UNAVAILABLE');
  });

  it('compares two analyzed revisions and forwards options snake_case', async () => {
    const draftId = await createDraft('lyrics');
    const baseHash = await analyze(draftId, 'lyrics one');
    const targetHash = await analyze(draftId, 'lyrics two');

    fastapiMock.analyzeDraftCompare.mockResolvedValue({
      analysis_id: 'cmp-1',
      language: 'en',
      title: null,
      previous: { revision_hash: baseHash, analysis: analyzeDraftFixture },
      current: { revision_hash: targetHash, analysis: analyzeDraftFixture },
      summary: {
        motif_delta_count: 1,
        repetition_delta_count: 0,
        section_delta_count: 0,
        consistency_delta_count: 0,
        family_counts: {},
        unmatched_previous_section_ids: [],
        unmatched_current_section_ids: [],
      },
      insights: [],
      capabilities: {
        compare_motifs: fullCap,
        compare_repetition: fullCap,
        compare_sections: fullCap,
        compare_consistency: fullCap,
      },
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft-compare')
      .send({
        draftId,
        baseRevisionHash: baseHash,
        targetRevisionHash: targetHash,
        options: { compareMotifs: true },
      });

    expect(res.status).toBe(201);
    expect(res.body.analysis_id).toBe('cmp-1');
    expect(res.body.previous.revision_hash).toBe(baseHash);
    expect(res.body.current.revision_hash).toBe(targetHash);

    const upstreamReq = fastapiMock.analyzeDraftCompare.mock.calls[0][0];
    expect(upstreamReq.options).toEqual({ compare_motifs: true });
    expect(upstreamReq.previous.content).toBe('lyrics one');
    expect(upstreamReq.current.content).toBe('lyrics two');
  });

  it('populates draft snapshot provenance after analyze', async () => {
    const draftId = await createDraft('lyrics');
    const hash = await analyze(draftId, 'lyrics');
    const res = await request(app.getHttpServer()).get(`/v1/drafts/${draftId}`);
    expect(res.status).toBe(200);
    expect(res.body.data.latest_analyzed_revision_hash).toBe(hash);
    expect(res.body.data.last_analysis_status).toBe('fresh');
    expect(typeof res.body.data.last_analyzed_at).toBe('string');
  });
});
