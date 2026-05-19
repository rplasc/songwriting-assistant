import { NotFoundException } from '@nestjs/common';
import { DraftsService } from './drafts.service';

describe('DraftsService', () => {
  let service: DraftsService;

  beforeEach(() => {
    service = new DraftsService();
  });

  it('creates a draft with provided title and content', () => {
    const draft = service.create({ title: 'Song 1', content: 'verse one' });
    expect(draft.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(draft.title).toBe('Song 1');
    expect(draft.content).toBe('verse one');
    expect(draft.language).toBe('en');
    expect(draft.createdAt).toBe(draft.updatedAt);
  });

  it('defaults title to "Untitled Draft" when omitted or empty', () => {
    expect(service.create({ content: 'x' }).title).toBe('Untitled Draft');
    expect(service.create({ title: '', content: 'x' }).title).toBe(
      'Untitled Draft',
    );
  });

  it('stores Spanish language when supplied', () => {
    const draft = service.create({ content: 'corazón', language: 'es' });
    expect(draft.language).toBe('es');
  });

  it('findById round-trips the created draft', () => {
    const created = service.create({ content: 'lyrics', language: 'es' });
    expect(service.findById(created.id)).toEqual(created);
  });

  it('findById throws NotFoundException with DRAFT_NOT_FOUND code', () => {
    try {
      service.findById('00000000-0000-0000-0000-000000000000');
      fail('expected NotFoundException');
    } catch (err) {
      expect(err).toBeInstanceOf(NotFoundException);
      const resp = (err as NotFoundException).getResponse() as {
        code: string;
      };
      expect(resp.code).toBe('DRAFT_NOT_FOUND');
    }
  });

  it('update merges fields, bumps updatedAt, keeps createdAt and id', async () => {
    const created = service.create({ title: 't1', content: 'c1' });
    await new Promise((r) => setTimeout(r, 5));
    const updated = service.update(created.id, { content: 'c2' });
    expect(updated.id).toBe(created.id);
    expect(updated.title).toBe('t1');
    expect(updated.content).toBe('c2');
    expect(updated.language).toBe('en');
    expect(updated.createdAt).toBe(created.createdAt);
    expect(updated.updatedAt > created.updatedAt).toBe(true);
  });

  it('update can change the draft language', () => {
    const created = service.create({ content: 'hello', language: 'en' });
    const updated = service.update(created.id, { language: 'es' });
    expect(updated.language).toBe('es');
    expect(updated.content).toBe('hello');
  });

  it('update throws NotFoundException for unknown id', () => {
    expect(() =>
      service.update('00000000-0000-0000-0000-000000000000', { title: 'x' }),
    ).toThrow(NotFoundException);
  });
});
