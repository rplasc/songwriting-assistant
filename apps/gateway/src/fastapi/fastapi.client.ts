import { HttpService } from '@nestjs/axios';
import {
  BadGatewayException,
  BadRequestException,
  HttpException,
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';
import { AxiosError } from 'axios';
import { firstValueFrom } from 'rxjs';
import {
  AnalyzeDraftCompareRequest,
  AnalyzeDraftRequest,
  AnalyzeLineRequest,
  RhymesRequest,
} from './dto/fastapi-requests';
import {
  DraftAnalysisResponse,
  DraftCompareResponse,
  LineAnalysisResponse,
  RhymeResponse,
} from './dto/fastapi-responses';

interface FastapiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
}

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

  async analyzeDraft(req: AnalyzeDraftRequest): Promise<DraftAnalysisResponse> {
    return this.post<DraftAnalysisResponse>('/v1/analyze-draft', req);
  }

  async analyzeDraftCompare(
    req: AnalyzeDraftCompareRequest,
  ): Promise<DraftCompareResponse> {
    return this.post<DraftCompareResponse>('/v1/analyze-draft-compare', req);
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    try {
      const res = await firstValueFrom(this.http.post<T>(path, body));
      return res.data;
    } catch (err) {
      throw this.mapError(err, path);
    }
  }

  private mapError(err: unknown, path: string): HttpException {
    const ax = err as AxiosError<FastapiErrorEnvelope>;
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
      const status = ax.response.status;
      // FastAPI returns 422 for caller-side validation errors (unsupported
      // language/mode, malformed payload). These are client problems, not
      // upstream gateway problems — surface them as 400 with the FastAPI
      // error code preserved so the editor can show a precise message.
      if (status === 422) {
        const envelope = ax.response.data;
        const code = envelope?.error?.code ?? 'upstream_validation_error';
        const message =
          envelope?.error?.message ?? 'Upstream validation failed.';
        this.logger.warn(
          `FastAPI 422 (${code}) calling ${path}: ${message}`,
        );
        return new BadRequestException({ code, message });
      }
      this.logger.warn(`FastAPI ${status} calling ${path}`);
      return new BadGatewayException('Upstream analysis failed');
    }
    this.logger.error(`Unexpected FastAPI error calling ${path}`, err as Error);
    return new BadGatewayException('Upstream analysis failed');
  }
}
