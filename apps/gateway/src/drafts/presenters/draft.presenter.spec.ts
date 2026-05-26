import { DraftPresenter } from './draft.presenter';
import { Draft } from '../draft.types';

describe('DraftPresenter', () => {
  it('maps internal Draft to snake_case payload with null snapshot fields by default', () => {
    const presenter = new DraftPresenter();
    const draft: Draft = {
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      language: 'es',
      version: 1,
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-02T00:00:00.000Z',
    };
    expect(presenter.toClient(draft)).toEqual({
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      language: 'es',
      sections: [],
      version: 1,
      created_at: '2026-01-01T00:00:00.000Z',
      updated_at: '2026-01-02T00:00:00.000Z',
      last_analyzed_at: null,
      last_analysis_status: null,
      latest_analyzed_revision_hash: null,
    });
  });

  it('emits sections in snake_case shape', () => {
    const presenter = new DraftPresenter();
    const draft: Draft = {
      id: 'abc',
      title: 't',
      content: 'a\nb\nc',
      language: 'en',
      sections: [
        { id: 'sec-1', label: 'verse', lineStart: 1, lineEnd: 2 },
        { id: 'sec-2', label: 'chorus', lineStart: 3, lineEnd: 3 },
      ],
      version: 1,
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-01T00:00:00.000Z',
    };
    expect(presenter.toClient(draft).sections).toEqual([
      { id: 'sec-1', label: 'verse', line_start: 1, line_end: 2 },
      { id: 'sec-2', label: 'chorus', line_start: 3, line_end: 3 },
    ]);
  });

  it('passes through populated snapshot provenance fields', () => {
    const presenter = new DraftPresenter();
    const draft: Draft = {
      id: 'abc',
      title: 't',
      content: 'lyrics',
      language: 'en',
      version: 2,
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-02T00:00:00.000Z',
      lastAnalyzedAt: '2026-01-02T00:01:00.000Z',
      lastAnalysisStatus: 'fresh',
      latestAnalyzedRevisionHash: 'abc123',
    };
    const out = presenter.toClient(draft);
    expect(out.last_analyzed_at).toBe('2026-01-02T00:01:00.000Z');
    expect(out.last_analysis_status).toBe('fresh');
    expect(out.latest_analyzed_revision_hash).toBe('abc123');
  });
});
