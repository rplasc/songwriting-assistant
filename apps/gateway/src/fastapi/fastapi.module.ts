import { HttpModule } from '@nestjs/axios';
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigType } from '@nestjs/config';
import fastapiConfig from '../config/fastapi.config';
import { FastapiClient } from './fastapi.client';

@Module({
  imports: [
    ConfigModule.forFeature(fastapiConfig),
    HttpModule.registerAsync({
      imports: [ConfigModule.forFeature(fastapiConfig)],
      inject: [fastapiConfig.KEY],
      useFactory: (cfg: ConfigType<typeof fastapiConfig>) => ({
        baseURL: cfg.baseUrl,
        timeout: cfg.timeoutMs,
      }),
    }),
  ],
  providers: [FastapiClient],
  exports: [FastapiClient],
})
export class FastapiModule {}
