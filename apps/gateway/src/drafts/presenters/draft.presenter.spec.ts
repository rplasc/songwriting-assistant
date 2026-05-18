import { DraftPresenter } from './draft.presenter';
import { Draft } from '../draft.types';

describe('DraftPresenter', () => {
  it('maps internal Draft to snake_case payload', () => {
    const presenter = new DraftPresenter();
    const draft: Draft = {
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      createdAt: '2026-01-01T00:00:00.000Z',
      updatedAt: '2026-01-02T00:00:00.000Z',
    };
    expect(presenter.toClient(draft)).toEqual({
      id: 'abc',
      title: 'Untitled Draft',
      content: 'lyrics',
      created_at: '2026-01-01T00:00:00.000Z',
      updated_at: '2026-01-02T00:00:00.000Z',
    });
  });
});
