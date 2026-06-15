import { Logger } from '@nestjs/common';
import {
  ConnectedSocket,
  MessageBody,
  SubscribeMessage,
  WebSocketGateway,
} from '@nestjs/websockets';
import { plainToInstance } from 'class-transformer';
import { validate } from 'class-validator';
import { randomUUID } from 'crypto';
import { Socket } from 'socket.io';
import { AnalyzeLineDto } from './dto/analyze-line.dto';
import { EditorService } from './editor.service';

/**
 * Line-level live analysis only. Draft-level review
 * (`/v1/editor/analyze-draft`, `/v1/editor/analyze-draft-compare`) is
 * HTTP-only by design — heavyweight review flows never share this transport.
 */
@WebSocketGateway({
  namespace: '/editor',
  cors: { origin: process.env.CORS_ORIGIN ?? '*' },
})
export class EditorGateway {
  private readonly logger = new Logger(EditorGateway.name);

  constructor(private readonly editor: EditorService) {}

  @SubscribeMessage('editor.analyze')
  async onAnalyze(
    @MessageBody() payload: unknown,
    @ConnectedSocket() client: Socket,
  ): Promise<void> {
    const dto = plainToInstance(AnalyzeLineDto, payload ?? {});
    const errors = await validate(dto);
    if (errors.length > 0) {
      client.emit('editor.error', {
        message: 'Invalid payload',
        code: 'VALIDATION_FAILED',
      });
      return;
    }

    const requestId = randomUUID();
    try {
      const result = await this.editor.analyze(dto.line, {
        requestId,
        targetWord: dto.target_word,
        rhymeMode: dto.rhyme_mode,
        language: dto.language,
        skipRhymes: dto.skip_rhymes,
      });
      client.emit('editor.analysis', result);
    } catch (err) {
      this.logger.error(
        `editor.analyze failed (request_id=${requestId})`,
        err as Error,
      );
      client.emit('editor.error', {
        message: 'Unable to analyze line',
        code: 'ANALYSIS_FAILED',
      });
    }
  }
}
