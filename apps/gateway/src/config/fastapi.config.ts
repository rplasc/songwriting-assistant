import { registerAs } from '@nestjs/config';

export interface FastapiConfig {
  baseUrl: string;
  timeoutMs: number;
}

export default registerAs(
  'fastapi',
  (): FastapiConfig => ({
    baseUrl: process.env.FASTAPI_BASE_URL ?? 'http://localhost:8000',
    timeoutMs: parseInt(process.env.FASTAPI_TIMEOUT_MS ?? '5000', 10),
  }),
);
