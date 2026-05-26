import { SnapshotStore } from './snapshot.store';
import { DraftSnapshot } from './snapshot.types';

function snap(hash: string): DraftSnapshot {
  return {
    revisionHash: hash,
    analyzedAt: new Date().toISOString(),
    content: `content-${hash}`,
    sections: [],
    analysisStatus: 'fresh',
    capabilities: {} as DraftSnapshot['capabilities'],
  };
}

describe('SnapshotStore', () => {
  let store: SnapshotStore;

  beforeEach(() => {
    store = new SnapshotStore();
  });

  it('returns null when no snapshot exists', () => {
    expect(store.find('d1', 'h1')).toBeNull();
  });

  it('roundtrips a put/find', () => {
    store.put('d1', snap('h1'));
    expect(store.find('d1', 'h1')?.content).toBe('content-h1');
  });

  it('keeps snapshots isolated per draft', () => {
    store.put('d1', snap('h1'));
    expect(store.find('d2', 'h1')).toBeNull();
  });

  it('clear removes all snapshots for a draft', () => {
    store.put('d1', snap('h1'));
    store.put('d1', snap('h2'));
    store.clear('d1');
    expect(store.find('d1', 'h1')).toBeNull();
    expect(store.find('d1', 'h2')).toBeNull();
  });

  it('evicts the oldest snapshot once the ring exceeds the max', () => {
    for (let i = 0; i < 20; i++) {
      store.put('d1', snap(`h${i}`));
    }
    // First 4 should be evicted (20 - 16 = 4)
    expect(store.find('d1', 'h0')).toBeNull();
    expect(store.find('d1', 'h3')).toBeNull();
    expect(store.find('d1', 'h4')).not.toBeNull();
    expect(store.find('d1', 'h19')).not.toBeNull();
  });

  it('re-putting an existing hash bumps it to most-recent (avoiding eviction)', () => {
    for (let i = 0; i < 16; i++) {
      store.put('d1', snap(`h${i}`));
    }
    store.put('d1', snap('h0')); // touch h0
    store.put('d1', snap('h99')); // forces an eviction of h1 (now oldest), not h0
    expect(store.find('d1', 'h0')).not.toBeNull();
    expect(store.find('d1', 'h1')).toBeNull();
  });
});
