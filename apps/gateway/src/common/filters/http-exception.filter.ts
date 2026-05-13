import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost): void {
    if (host.getType() !== 'http') {
      throw exception;
    }
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const req = ctx.getRequest<Request>();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let code = 'INTERNAL_ERROR';
    let message = 'Internal server error';

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const resp = exception.getResponse();
      const respMessage =
        typeof resp === 'string'
          ? resp
          : ((resp as { message?: string | string[] }).message ??
            exception.message);
      message = Array.isArray(respMessage) ? respMessage[0] : respMessage;
      code = this.codeFor(status, exception);
    } else {
      this.logger.error(
        `Unhandled error on ${req.method} ${req.url}`,
        exception as Error,
      );
    }

    res.status(status).json({ error: { code, message } });
  }

  private codeFor(status: number, exc: HttpException): string {
    if (status === HttpStatus.SERVICE_UNAVAILABLE) return 'FASTAPI_UNAVAILABLE';
    if (status === HttpStatus.BAD_GATEWAY) return 'UPSTREAM_FAILED';
    if (status === HttpStatus.BAD_REQUEST) return 'VALIDATION_FAILED';
    if (status === HttpStatus.NOT_FOUND) return 'NOT_FOUND';
    return exc.name?.replace(/Exception$/, '').toUpperCase() || 'ERROR';
  }
}
