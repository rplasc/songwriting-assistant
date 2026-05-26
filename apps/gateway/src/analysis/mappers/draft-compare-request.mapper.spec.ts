import { DraftSnapshot } from '../../drafts/snapshot.types';
import { DraftCompareRequestMapper } from './draft-compare-request.mapper';

function snap(overrides: Partial<DraftSnapshot> = {}): DraftSnapshot {
  return {
    revisionHash: 'h',
    analyzedAt: '2026-01-01T00:00:00.000Z',
    content: 'lyrics',
    sections: [],
    analysisStatus: 'fresh',
    capabilities: {} as DraftSnapshot['capabilities'],
    ...overrides,
  };
}

describe('DraftCompareRequestMapper', () => {
  const mapper = new DraftCompareRequestMapper();

  it('builds upstream request with default language and previous/current sides', () => {
    const out = mapper.resolve({
      base: snap({ content: 'old' }),
      target: snap({ content: 'new' }),
    });
    expect(out.language).toBe('en');
    expect(out.previous.content).toBe('old');
    expect(out.current.content).toBe('new');
    expect(out.options).toBeUndefined();
  });

  it('maps camelCase compare options to snake_case upstream options', () => {
    const out = mapper.resolve({
      base: snap(),
      target: snap(),
      options: {
        compareMotifs: true,
        compareConsistency: false,
      },
    });
    expect(out.options).toEqual({
      compare_motifs: true,
      compare_consistency: false,
    });
  });

  it('forwards sections in snake_case and omits empty section arrays', () => {
    const out = mapper.resolve({
      base: snap({
        sections: [
          { id: 's1', label: 'verse', lineStart: 1, lineEnd: 2 },
        ],
      }),
      target: snap(),
    });
    expect(out.previous.sections).toEqual([
      { id: 's1', label: 'verse', line_start: 1, line_end: 2 },
    ]);
    expect(out.current.sections).toBeUndefined();
  });
});
