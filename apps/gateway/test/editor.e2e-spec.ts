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
        {
          text: 'fire',
          normalized: 'fire',
          syllables: 2,
          pronunciation_found: true,
        },
      ],
      last_word: {
        text: 'eyes',
        normalized: 'eyes',
        pronunciation_found: true,
      },
    });
    fastapiMock.getRhymes.mockResolvedValue({
      word: 'eyes',
      normalized_word: 'eyes',
      pronunciations_found: true,
      rhymes: [
        { word: 'skies', syllables: 1, rhyme_type: 'perfect', score: 0.9 },
      ],
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

  it('forwards rhyme_mode=near to FastAPI and echoes it on the response', async () => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: 'I see the fire in your eyes',
      normalized_line: 'i see the fire in your eyes',
      total_syllables: 8,
      tokens: [],
      last_word: {
        text: 'eyes',
        normalized: 'eyes',
        pronunciation_found: true,
      },
    });
    fastapiMock.getRhymes.mockResolvedValue({
      word: 'eyes',
      normalized_word: 'eyes',
      pronunciations_found: true,
      rhymes: [{ word: 'lies', syllables: 1, rhyme_type: 'near', score: 0.7 }],
      meta: { limit: 10, include_near: true },
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'I see the fire in your eyes', rhyme_mode: 'near' });

    expect(res.status).toBe(201);
    expect(fastapiMock.getRhymes).toHaveBeenCalledWith({
      word: 'eyes',
      rhyme_mode: 'near',
    });
    expect(res.body.rhymes.mode).toBe('near');
  });

  it('rejects unknown rhyme_mode with VALIDATION_FAILED', async () => {
    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'hello world', rhyme_mode: 'slant' });
    expect(res.status).toBe(400);
    expect(res.body.error.code).toBe('VALIDATION_FAILED');
  });

  it('still calls NLP for unknown last_word so the heuristic fallback can run', async () => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: 'wundurful',
      normalized_line: 'wundurful',
      total_syllables: 3,
      tokens: [],
      last_word: {
        text: 'wundurful',
        normalized: 'wundurful',
        pronunciation_found: false,
      },
    });
    fastapiMock.getRhymes.mockResolvedValue({
      word: 'wundurful',
      normalized_word: 'wundurful',
      pronunciations_found: true,
      rhymes: [
        { word: 'beautiful', syllables: 3, rhyme_type: 'family', score: 0.7 },
      ],
      meta: { limit: 10, include_near: false },
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: 'wundurful' });

    expect(res.status).toBe(201);
    expect(fastapiMock.getRhymes).toHaveBeenCalledWith({
      word: 'wundurful',
      rhyme_mode: 'perfect',
    });
    expect(res.body.rhymes.items).toEqual([
      { word: 'beautiful', syllables: 3, type: 'family' },
    ]);
  });

  it('returns empty items when there is no last_word at all', async () => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: '...',
      normalized_line: '',
      total_syllables: 0,
      tokens: [],
      last_word: null,
    });

    const res = await request(app.getHttpServer())
      .post('/v1/editor/analyze')
      .send({ line: '...' });

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
