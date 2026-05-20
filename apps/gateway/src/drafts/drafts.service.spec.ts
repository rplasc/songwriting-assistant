import { BadRequestException, NotFoundException } from '@nestjs/common';
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

  it('remove deletes the draft so subsequent reads fail', () => {
    const created = service.create({ content: 'gone soon' });
    service.remove(created.id);
    expect(() => service.findById(created.id)).toThrow(NotFoundException);
  });

  it('remove throws NotFoundException for unknown id', () => {
    expect(() =>
      service.remove('00000000-0000-0000-0000-000000000000'),
    ).toThrow(NotFoundException);
  });

  describe('sections', () => {
    it('creates a draft with sorted sections and assigns UUIDs', () => {
      const draft = service.create({
        content: 'a\nb\nc\nd',
        sections: [
          { label: 'chorus', lineStart: 3, lineEnd: 4 },
          { label: 'verse', lineStart: 1, lineEnd: 2 },
        ],
      });
      expect(draft.sections).toHaveLength(2);
      expect(draft.sections?.[0].label).toBe('verse');
      expect(draft.sections?.[1].label).toBe('chorus');
      for (const s of draft.sections ?? []) {
        expect(s.id).toMatch(
          /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
        );
      }
    });

    it('rejects overlapping sections', () => {
      expect(() =>
        service.create({
          content: 'a\nb\nc',
          sections: [
            { label: 'verse', lineStart: 1, lineEnd: 2 },
            { label: 'chorus', lineStart: 2, lineEnd: 3 },
          ],
        }),
      ).toThrow(BadRequestException);
    });

    it('rejects section lineEnd beyond content line count', () => {
      expect(() =>
        service.create({
          content: 'only one line',
          sections: [{ label: 'verse', lineStart: 1, lineEnd: 5 }],
        }),
      ).toThrow(BadRequestException);
    });

    it('rejects lineStart greater than lineEnd', () => {
      expect(() =>
        service.create({
          content: 'a\nb\nc',
          sections: [{ label: 'verse', lineStart: 3, lineEnd: 1 }],
        }),
      ).toThrow(BadRequestException);
    });

    it('update with sections re-validates against new content', () => {
      const created = service.create({ content: 'a\nb\nc' });
      const updated = service.update(created.id, {
        content: 'a\nb',
        sections: [{ label: 'verse', lineStart: 1, lineEnd: 2 }],
      });
      expect(updated.sections).toHaveLength(1);
      expect(updated.sections?.[0].lineEnd).toBe(2);
    });
  });
});
