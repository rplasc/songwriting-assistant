import { INestApplication } from '@nestjs/common';
import { IoAdapter } from '@nestjs/platform-socket.io';
import { Test } from '@nestjs/testing';
import { AddressInfo } from 'net';
import { io as ioClient, Socket } from 'socket.io-client';
import { AppModule } from '../src/app.module';
import { FastapiClient } from '../src/fastapi/fastapi.client';

describe('Editor WS (e2e)', () => {
  let app: INestApplication;
  let url: string;
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
    app.useWebSocketAdapter(new IoAdapter(app));
    await app.listen(0);

    const addr = app.getHttpServer().address() as AddressInfo;
    url = `http://localhost:${addr.port}/editor`;
  });

  afterAll(async () => {
    await app.close();
  });

  function connect(): Socket {
    return ioClient(url, { transports: ['websocket'], forceNew: true });
  }

  it('emits editor.analysis for a valid line', (done) => {
    fastapiMock.analyzeLine.mockResolvedValue({
      line: 'Broken dreams in neon light',
      normalized_line: 'broken dreams in neon light',
      total_syllables: 7,
      tokens: [],
      last_word: { text: 'light', normalized: 'light', pronunciation_found: true },
    });
    fastapiMock.getRhymes.mockResolvedValue({
      word: 'light',
      normalized_word: 'light',
      pronunciations_found: true,
      rhymes: [{ word: 'night', syllables: 1, rhyme_type: 'perfect', score: 0.9 }],
      meta: { limit: 10, include_near: false },
    });

    const sock = connect();
    sock.on('editor.analysis', (payload) => {
      try {
        expect(payload.line).toBe('Broken dreams in neon light');
        expect(payload.rhymes.target_word).toBe('light');
        expect(payload.rhymes.items[0]).toEqual({
          word: 'night',
          syllables: 1,
          type: 'perfect',
        });
        sock.close();
        done();
      } catch (e) {
        sock.close();
        done(e);
      }
    });
    sock.on('connect', () =>
      sock.emit('editor.analyze', { line: 'Broken dreams in neon light' }),
    );
  });

  it('emits editor.error with VALIDATION_FAILED for empty payload', (done) => {
    const sock = connect();
    sock.on('editor.error', (payload) => {
      try {
        expect(payload.code).toBe('VALIDATION_FAILED');
        sock.close();
        done();
      } catch (e) {
        sock.close();
        done(e);
      }
    });
    sock.on('connect', () => sock.emit('editor.analyze', { line: '   ' }));
  });
});
