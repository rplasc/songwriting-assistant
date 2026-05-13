import { Injectable } from '@nestjs/common';
import { performance } from 'perf_hooks';
import { FastapiClient } from '../fastapi/fastapi.client';
import {
  EditorAnalysisPayload,
  EditorResponsePresenter,
} from './presenters/editor-response.presenter';

@Injectable()
export class EditorService {
  constructor(
    private readonly fastapi: FastapiClient,
    private readonly presenter: EditorResponsePresenter,
  ) {}

  async analyze(
    line: string,
    requestId?: string,
  ): Promise<EditorAnalysisPayload> {
    const t0 = performance.now();
    const lineResp = await this.fastapi.analyzeLine({ line });

    const last = lineResp.last_word;
    const rhymes =
      last && last.pronunciation_found
        ? await this.fastapi.getRhymes({ word: last.normalized })
        : null;

    return this.presenter.toClient(
      lineResp,
      rhymes,
      performance.now() - t0,
      requestId,
    );
  }
}
