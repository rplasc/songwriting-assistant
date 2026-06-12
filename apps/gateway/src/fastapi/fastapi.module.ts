import { HttpModule } from '@nestjs/axios';
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigType } from '@nestjs/config';
import { Agent as HttpAgent } from 'http';
import { Agent as HttpsAgent } from 'https';
import fastapiConfig from '../config/fastapi.config';
import { FastapiClient } from './fastapi.client';

// Shared keep-alive agents so the per-keystroke gateway -> NLP traffic
// (analyze-line, rhymes) reuses connections instead of reconnecting on every
// request, regardless of the Node version's default agent settings.
const httpAgent = new HttpAgent({ keepAlive: true });
const httpsAgent = new HttpsAgent({ keepAlive: true });

@Module({
  imports: [
    ConfigModule.forFeature(fastapiConfig),
    HttpModule.registerAsync({
      imports: [ConfigModule.forFeature(fastapiConfig)],
      inject: [fastapiConfig.KEY],
      useFactory: (cfg: ConfigType<typeof fastapiConfig>) => ({
        baseURL: cfg.baseUrl,
        timeout: cfg.timeoutMs,
        httpAgent,
        httpsAgent,
      }),
    }),
  ],
  providers: [FastapiClient],
  exports: [FastapiClient],
})
export class FastapiModule {}
