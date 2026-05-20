import {
  BadGatewayException,
  BadRequestException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { of, throwError } from 'rxjs';
import { AxiosError, AxiosResponse } from 'axios';
import { FastapiClient } from './fastapi.client';

function axiosErr(code: string, response?: Partial<AxiosResponse>): AxiosError {
  const err = new Error('boom') as AxiosError;
  err.code = code;
  if (response) err.response = response as AxiosResponse;
  return err;
}

describe('FastapiClient', () => {
  let http: jest.Mocked<HttpService>;
  let client: FastapiClient;

  beforeEach(() => {
    http = {
      get: jest.fn(),
      post: jest.fn(),
    } as unknown as jest.Mocked<HttpService>;
    client = new FastapiClient(http);
  });

  it('ping returns true on 200', async () => {
    (http.get as jest.Mock).mockReturnValue(of({ status: 200 }));
    await expect(client.ping()).resolves.toBe(true);
  });

  it('ping returns false on any error', async () => {
    (http.get as jest.Mock).mockReturnValue(throwError(() => new Error()));
    await expect(client.ping()).resolves.toBe(false);
  });

  it('maps timeout to ServiceUnavailable', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() => axiosErr('ECONNABORTED')),
    );
    await expect(client.analyzeLine({ line: 'hi' })).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });

  it('maps ECONNREFUSED to ServiceUnavailable', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() => axiosErr('ECONNREFUSED')),
    );
    await expect(client.getRhymes({ word: 'a' })).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });

  it('maps non-2xx response to BadGateway', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() => axiosErr('ERR', { status: 500, data: {} })),
    );
    await expect(client.analyzeLine({ line: 'hi' })).rejects.toBeInstanceOf(
      BadGatewayException,
    );
  });

  it('maps FastAPI 422 unsupported_language to BadRequest, preserving the code', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() =>
        axiosErr('ERR', {
          status: 422,
          data: {
            error: {
              code: 'unsupported_language',
              message: "language 'fr' is not supported.",
            },
          },
        }),
      ),
    );
    try {
      await client.getRhymes({ word: 'a', language: 'en' });
      fail('expected BadRequestException');
    } catch (err) {
      expect(err).toBeInstanceOf(BadRequestException);
      const resp = (err as BadRequestException).getResponse() as {
        code: string;
        message: string;
      };
      expect(resp.code).toBe('unsupported_language');
      expect(resp.message).toContain("language 'fr'");
    }
  });

  it('maps FastAPI 422 unsupported_mode to BadRequest', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() =>
        axiosErr('ERR', {
          status: 422,
          data: {
            error: {
              code: 'unsupported_mode',
              message: "mode 'perfect' is not supported for language 'es'.",
            },
          },
        }),
      ),
    );
    await expect(
      client.getRhymes({ word: 'corazón', language: 'es', mode: 'perfect' }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('analyzeDraft posts to /v1/analyze-draft and returns data on success', async () => {
    const upstream = {
      language: 'en',
      summary: { section_count: 1, line_count: 2 },
      sections: [{ id: 's1', label: 'verse', line_start: 1, line_end: 2 }],
      insights: [],
      capabilities: { rhyme_scheme: true, cadence: true, repetition: true },
    };
    (http.post as jest.Mock).mockReturnValue(of({ data: upstream }));
    const out = await client.analyzeDraft({ content: 'a\nb' });
    expect(http.post).toHaveBeenCalledWith('/v1/analyze-draft', {
      content: 'a\nb',
    });
    expect(out).toEqual(upstream);
  });

  it('analyzeDraft maps FastAPI 422 to BadRequest', async () => {
    (http.post as jest.Mock).mockReturnValue(
      throwError(() =>
        axiosErr('ERR', {
          status: 422,
          data: { error: { code: 'invalid_sections', message: 'bad' } },
        }),
      ),
    );
    await expect(
      client.analyzeDraft({ content: 'x' }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('returns data on success', async () => {
    (http.post as jest.Mock).mockReturnValue(
      of({
        data: {
          line: 'hi',
          total_syllables: 1,
          tokens: [],
          last_word: null,
          normalized_line: 'hi',
          language: 'en',
        },
      }),
    );
    const out = await client.analyzeLine({ line: 'hi' });
    expect(out.line).toBe('hi');
    expect(out.language).toBe('en');
  });
});
