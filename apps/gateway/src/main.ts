import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { IoAdapter } from '@nestjs/platform-socket.io';
import { AppModule } from './app.module';
import { HttpExceptionFilter } from './common/filters/http-exception.filter';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';
import { AppConfig } from './config/app.config';
import { FastapiConfig } from './config/fastapi.config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const config = app.get(ConfigService);
  const appCfg = config.get<AppConfig>('app')!;
  const fastapiCfg = config.get<FastapiConfig>('fastapi')!;

  app.enableCors({ origin: appCfg.corsOrigin, credentials: true });
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );
  app.useGlobalFilters(new HttpExceptionFilter());
  app.useGlobalInterceptors(new LoggingInterceptor());
  app.useWebSocketAdapter(new IoAdapter(app));

  await app.listen(appCfg.port);
  Logger.log(
    `Gateway listening on :${appCfg.port} (FastAPI=${fastapiCfg.baseUrl}, timeout=${fastapiCfg.timeoutMs}ms)`,
    'Bootstrap',
  );
}
bootstrap();
