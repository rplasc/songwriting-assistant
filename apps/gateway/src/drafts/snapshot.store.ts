import { Injectable } from '@nestjs/common';
import { DraftSnapshot } from './snapshot.types';

const SNAPSHOT_RING_MAX = 16;

@Injectable()
export class SnapshotStore {
  private readonly byDraft = new Map<string, Map<string, DraftSnapshot>>();

  put(draftId: string, snapshot: DraftSnapshot): void {
    let ring = this.byDraft.get(draftId);
    if (!ring) {
      ring = new Map<string, DraftSnapshot>();
      this.byDraft.set(draftId, ring);
    }
    // Re-insert to bump to most-recent position even on duplicate hash.
    ring.delete(snapshot.revisionHash);
    ring.set(snapshot.revisionHash, snapshot);
    while (ring.size > SNAPSHOT_RING_MAX) {
      const oldest = ring.keys().next().value;
      if (oldest === undefined) break;
      ring.delete(oldest);
    }
  }

  find(draftId: string, revisionHash: string): DraftSnapshot | null {
    return this.byDraft.get(draftId)?.get(revisionHash) ?? null;
  }

  clear(draftId: string): void {
    this.byDraft.delete(draftId);
  }
}
