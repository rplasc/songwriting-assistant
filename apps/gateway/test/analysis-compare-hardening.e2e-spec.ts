import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/app.module';
import { HttpExceptionFilter } from '../src/common/filters/http-exception.filter';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Analyze Draft Compare — hardening (e2e)', () => {
  let app: INestApplication<App>;
  const fullCap = { status: 'full' as const, reason_code: null };
  const offCap = {
    status: 'unsupported' as const,
    reason_code: 'language_unsupported' as const,
  };
  const partialMixed = {
    status: 'partial' as const,
    reason_code: 'language_partial_support' as const,
  };

  function caps(overrides: Record<string, unknown> = {}) {
    return {
      rhyme_scheme: fullCap,
      cadence_patterns: fullCap,
      stress_hints: offCap,
      repetition: fullCap,
      mixed_language: offCap,
      semantic_repetition: offCap,
      motif_tracking: offCap,
      section_contrast: offCap,
      consistency_hints: offCap,
      ...overrides,
    };
  }

  function analysisFixture(capabilitiesOverrides: Record<string, unknown> = {}) {
    return {
      language: 'en',
      title: null,
      capabilities: caps(capabilitiesOverrides),
      summary: {
        section_count: 0,
        line_count: 1,
        total_syllables: 4,
        notable_patterns: [],
      },
      insights: [],
      detail: { sections: [] },
    };
  }

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

  async function createDraft(content: string, language = 'en'): Promise<string> {
    const res = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content, title: 't', language });
    expect(res.status).toBe(201);
    return res.body.data.id as string;
  }

  async function analyze(
    draftId: string,
    content: string,
    fixture = analysisFixture(),
  ): Promise<string> {
    fastapiMock.analyzeDraft.mockResolvedValueOnce(fixture);
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft')
      .send({ draftId, content });
    expect(res.status).toBe(201);
    return res.body.revision_hash as string;
  }

  it('evicts the oldest snapshot after the 16-entry ring fills up', async () => {
    const draftId = await createDraft('seed');
    const firstHash = await analyze(draftId, 'rev-0');
    for (let i = 1; i < 17; i++) {
      await analyze(draftId, `rev-${i}`);
    }
    // 17 distinct analyses → first one evicted. Try to use it as a baseline.
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft-compare')
      .send({
        draftId,
        baseRevisionHash: firstHash,
        targetRevisionHash: firstHash,
      });
    expect(res.status).toBe(400);
    expect(res.body.error?.code).toBe('COMPARE_BASELINE_UNAVAILABLE');
    expect(res.body.error?.details?.missing).toBe('base');
  });

  it('leaves provenance fields unchanged after a PATCH (client derives stale-ness)', async () => {
    const draftId = await createDraft('lyrics one');
    const hash = await analyze(draftId, 'lyrics one');

    const patchRes = await request(app.getHttpServer())
      .patch(`/v1/drafts/${draftId}`)
      .send({ content: 'lyrics one but edited' });
    expect(patchRes.status).toBe(200);

    const getRes = await request(app.getHttpServer()).get(
      `/v1/drafts/${draftId}`,
    );
    expect(getRes.status).toBe(200);
    // Provenance points at the *analyzed* revision, not the now-current content.
    expect(getRes.body.data.latest_analyzed_revision_hash).toBe(hash);
    expect(getRes.body.data.last_analysis_status).toBe('fresh');
    expect(typeof getRes.body.data.last_analyzed_at).toBe('string');
    // Current content differs → client computes staleness by re-hashing.
    expect(getRes.body.data.content).toBe('lyrics one but edited');
  });

  it('permits compare with identical base and target hashes', async () => {
    const draftId = await createDraft('lyrics');
    const hash = await analyze(draftId, 'lyrics');
    fastapiMock.analyzeDraftCompare.mockResolvedValue({
      analysis_id: 'cmp-same',
      language: 'en',
      title: null,
      previous: { revision_hash: hash, analysis: analysisFixture() },
      current: { revision_hash: hash, analysis: analysisFixture() },
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
        baseRevisionHash: hash,
        targetRevisionHash: hash,
      });
    expect(res.status).toBe(201);
    expect(res.body.previous.revision_hash).toBe(hash);
    expect(res.body.current.revision_hash).toBe(hash);
  });

  it('accepts forceRefresh on compare but never forwards it to FastAPI', async () => {
    const draftId = await createDraft('lyrics');
    const base = await analyze(draftId, 'rev-a');
    const target = await analyze(draftId, 'rev-b');
    fastapiMock.analyzeDraftCompare.mockResolvedValue({
      analysis_id: 'cmp-fr',
      language: 'en',
      title: null,
      previous: { revision_hash: base, analysis: analysisFixture() },
      current: { revision_hash: target, analysis: analysisFixture() },
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
        baseRevisionHash: base,
        targetRevisionHash: target,
        forceRefresh: true,
      });
    expect(res.status).toBe(201);
    const upstreamReq = fastapiMock.analyzeDraftCompare.mock.calls[0][0];
    expect(upstreamReq).not.toHaveProperty('force_refresh');
    expect(upstreamReq).not.toHaveProperty('forceRefresh');
  });

  it('surfaces partial bilingual capability with reason_code intact', async () => {
    const draftId = await createDraft('corazón', 'es');
    fastapiMock.analyzeDraft.mockResolvedValueOnce({
      ...analysisFixture({ mixed_language: partialMixed }),
      language: 'es',
    });
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze-draft')
      .send({ draftId, content: 'corazón', language: 'es' });
    expect(res.status).toBe(201);
    expect(res.body.analysis.capabilities.mixed_language).toEqual({
      status: 'partial',
      reason_code: 'language_partial_support',
    });
    // Status should still be 'fresh' because partial counts as enabled.
    expect(res.body.analysis_status).toBe('fresh');
  });
});
