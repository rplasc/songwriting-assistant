import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/app.module';
import { HttpExceptionFilter } from '../src/common/filters/http-exception.filter';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Health (e2e)', () => {
  let app: INestApplication<App>;
  const fastapiMock = { ping: jest.fn() };

  beforeAll(async () => {
    process.env.FASTAPI_BASE_URL = 'http://localhost:9999';
    const mod = await Test.createTestingModule({ imports: [AppModule] })
      .overrideProvider(FastapiClient)
      .useValue(fastapiMock)
      .compile();

    app = mod.createNestApplication();
    app.useGlobalPipes(
      new ValidationPipe({ whitelist: true, transform: true }),
    );
    app.useGlobalFilters(new HttpExceptionFilter());
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('GET /health returns ok', async () => {
    const res = await request(app.getHttpServer()).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok', service: 'nestjs-api' });
  });

  it('GET /health/dependencies reflects FastAPI reachable', async () => {
    fastapiMock.ping.mockResolvedValueOnce(true);
    const res = await request(app.getHttpServer()).get('/health/dependencies');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      status: 'ok',
      fastapi: { reachable: true },
    });
  });

  it('GET /health/dependencies returns degraded when FastAPI unreachable', async () => {
    fastapiMock.ping.mockResolvedValueOnce(false);
    const res = await request(app.getHttpServer()).get('/health/dependencies');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('degraded');
    expect(res.body.fastapi.reachable).toBe(false);
  });
});
