import { HttpService } from '@nestjs/axios';
import {
  BadGatewayException,
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';
import { AxiosError } from 'axios';
import { firstValueFrom } from 'rxjs';
import { AnalyzeLineRequest, RhymesRequest } from './dto/fastapi-requests';
import { LineAnalysisResponse, RhymeResponse } from './dto/fastapi-responses';

@Injectable()
export class FastapiClient {
  private readonly logger = new Logger(FastapiClient.name);

  constructor(private readonly http: HttpService) {}

  async ping(): Promise<boolean> {
    try {
      const res = await firstValueFrom(this.http.get('/healthz'));
      return res.status === 200;
    } catch {
      return false;
    }
  }

  async analyzeLine(req: AnalyzeLineRequest): Promise<LineAnalysisResponse> {
    return this.post<LineAnalysisResponse>('/v1/analyze-line', req);
  }

  async getRhymes(req: RhymesRequest): Promise<RhymeResponse> {
    return this.post<RhymeResponse>('/v1/rhymes', req);
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    try {
      const res = await firstValueFrom(this.http.post<T>(path, body));
      return res.data;
    } catch (err) {
      throw this.mapError(err, path);
    }
  }

  private mapError(err: unknown, path: string): Error {
    const ax = err as AxiosError;
    if (ax?.code === 'ECONNABORTED' || ax?.code === 'ETIMEDOUT') {
      this.logger.warn(`FastAPI timeout calling ${path}`);
      return new ServiceUnavailableException('FastAPI unreachable');
    }
    if (
      ax?.code === 'ECONNREFUSED' ||
      ax?.code === 'ENOTFOUND' ||
      ax?.code === 'EAI_AGAIN'
    ) {
      this.logger.warn(`FastAPI unreachable (${ax.code}) calling ${path}`);
      return new ServiceUnavailableException('FastAPI unreachable');
    }
    if (ax?.response) {
      this.logger.warn(`FastAPI ${ax.response.status} calling ${path}`);
      return new BadGatewayException('Upstream analysis failed');
    }
    this.logger.error(`Unexpected FastAPI error calling ${path}`, err as Error);
    return new BadGatewayException('Upstream analysis failed');
  }
}
