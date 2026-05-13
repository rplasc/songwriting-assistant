import {
  INestApplication,
  ServiceUnavailableException,
  ValidationPipe,
} from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/app.module';
import { HttpExceptionFilter } from '../src/common/filters/http-exception.filter';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Editor (e2e)', () => {
  let app: INestApplication<App>;
  const fastapiMock = {
    ping: jest.fn().mockResolvedValue(true),
    analyzeLine: jest.fn(),
    getRhymes: jest.fn(),
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
    fastapiMock.analyzeLine.mockReset();
    fastapiMock.getRhymes.mockReset();
  });

  it('POST /v1/editor/analyze returns combined payload', async () => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: 'I see the fire in your eyes',
      normalized_line: 'i see the fire in your eyes',
      total_syllables: 8,
      tokens: [
        { text: 'fire', normalized: 'fire', syllables: 2, pronunciation_found: true },
      ],
      last_word: { text: 'eyes', normalized: 'eyes', pronunciation_found: true },
    });
    fastapiMock.getRhymes.mockResolvedValue({
      word: 'eyes',
      normalized_word: 'eyes',
      pronunciations_found: true,
      rhymes: [{ word: 'skies', syllables: 1, rhyme_type: 'perfect', score: 0.9 }],
      meta: { limit: 10, include_near: false },
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'I see the fire in your eyes' });

    expect(res.status).toBe(201);
    expect(res.body.line).toBe('I see the fire in your eyes');
    expect(res.body.syllables.total).toBe(8);
    expect(res.body.rhymes.target_word).toBe('eyes');
    expect(res.body.rhymes.items).toEqual([
      { word: 'skies', syllables: 1, type: 'perfect' },
    ]);
    expect(res.body.meta.latency_ms).toBeGreaterThanOrEqual(0);
  });

  it('returns empty items when last_word has no pronunciation', async () => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: 'asdfqwer',
      normalized_line: 'asdfqwer',
      total_syllables: 0,
      tokens: [],
      last_word: { text: 'asdfqwer', normalized: 'asdfqwer', pronunciation_found: false },
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'asdfqwer' });

    expect(res.status).toBe(201);
    expect(res.body.rhymes.items).toEqual([]);
    expect(fastapiMock.getRhymes).not.toHaveBeenCalled();
  });

  it('rejects empty line with VALIDATION_FAILED', async () => {
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: '   ' });
    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
  });

  it('maps FastAPI unreachable to 503 FASTAPI_UNAVAILABLE', async () => {
    fastapiMock.analyzeLine.mockRejectedValue(
      new ServiceUnavailableException('FastAPI unreachable'),
    );
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'hello world' });
    expect(res.status).toBe(503);
    expect(res.body.error.code).toBe('FASTAPI_UNAVAILABLE');
  });
});
