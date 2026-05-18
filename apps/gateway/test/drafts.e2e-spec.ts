import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/app.module';
import { HttpExceptionFilter } from '../src/common/filters/http-exception.filter';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Drafts (e2e)', () => {
  let app: INestApplication<App>;

  beforeAll(async () => {
    process.env.FASTAPI_BASE_URL = 'http://localhost:9999';
    const mod = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(FastapiClient)
      .useValue({
        ping: jest.fn().mockResolvedValue(true),
        analyzeLine: jest.fn(),
        getRhymes: jest.fn(),
      })
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

  it('POST /v1/drafts creates a draft (201)', async () => {
    const res = await request(app.getHttpServer()).post('/v1/drafts').send({
      title: 'Untitled Draft',
      content: 'I see the fire in your eyes',
    });

    expect(res.status).toBe(201);
    expect(res.body.data.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(res.body.data.title).toBe('Untitled Draft');
    expect(res.body.data.content).toBe('I see the fire in your eyes');
    expect(res.body.data.created_at).toBeDefined();
    expect(res.body.data.updated_at).toBeDefined();
  });

  it('defaults title when omitted', async () => {
    const res = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content: 'just content' });
    expect(res.status).toBe(201);
    expect(res.body.data.title).toBe('Untitled Draft');
  });

  it('GET /v1/drafts/:id returns a stored draft (200)', async () => {
    const created = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content: 'first line' });
    const { id } = created.body.data;

    const res = await request(app.getHttpServer()).get(`/v1/drafts/${id}`);
    expect(res.status).toBe(200);
    expect(res.body.data.id).toBe(id);
    expect(res.body.data.content).toBe('first line');
  });

  it('PATCH /v1/drafts/:id updates content and bumps updated_at (200)', async () => {
    const created = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content: 'original' });
    const { id, updated_at: originalUpdatedAt } = created.body.data;

    await new Promise((r) => setTimeout(r, 5));
    const res = await request(app.getHttpServer())
      .patch(`/v1/drafts/${id}`)
      .send({ content: 'revised' });

    expect(res.status).toBe(200);
    expect(res.body.data.content).toBe('revised');
    expect(res.body.data.updated_at > originalUpdatedAt).toBe(true);
  });

  it('returns 404 DRAFT_NOT_FOUND for unknown id', async () => {
    const res = await request(app.getHttpServer()).get(
      '/v1/drafts/00000000-0000-0000-0000-000000000000',
    );
    expect(res.status).toBe(404);
    expect(res.body.error.code).toBe('DRAFT_NOT_FOUND');
  });

  it('returns 400 VALIDATION_FAILED for malformed UUID', async () => {
    const res = await request(app.getHttpServer()).get('/v1/drafts/not-a-uuid');
    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
  });

  it('returns 400 when PATCH body is empty', async () => {
    const created = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ content: 'x' });
    const { id } = created.body.data;

    const res = await request(app.getHttpServer())
      .patch(`/v1/drafts/${id}`)
      .send({});

    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
  });

  it('rejects missing content on create with VALIDATION_FAILED', async () => {
    const res = await request(app.getHttpServer())
      .post('/v1/drafts')
      .send({ title: 'only title' });
    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
  });
});
