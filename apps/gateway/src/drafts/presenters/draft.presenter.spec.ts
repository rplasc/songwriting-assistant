import { DraftPresenter } from './draft.presenter';
import { Draft } from '../draft.types';

describe('DraftPresenter', () => {
  it('maps internal Draft to snake_case payload including language and empty sections', () => {
    const presenter = new DraftPresenter();
    const draft: Draft = {
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      language: 'es',
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-02T00:00:00.000Z',
    };
    expect(presenter.toClient(draft)).toEqual({
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      language: 'es',
      sections: [],
      created_at: '2026-01-01T00:00:00.000Z',
      updated_at: '2026-01-02T00:00:00.000Z',
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
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-01T00:00:00.000Z',
    };
    expect(presenter.toClient(draft).sections).toEqual([
      { id: 'sec-1', label: 'verse', line_start: 1, line_end: 2 },
      { id: 'sec-2', label: 'chorus', line_start: 3, line_end: 3 },
    ]);
  });
});
