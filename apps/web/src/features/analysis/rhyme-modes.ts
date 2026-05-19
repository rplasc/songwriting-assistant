export type RhymeMode = "perfect" | "near" | "consonant" | "assonant";

export type ClientRhymeMode = Extract<RhymeMode, "perfect" | "near">;

export const DEFAULT_RHYME_MODE: ClientRhymeMode = "perfect";

export const RHYME_MODE_OPTIONS: ReadonlyArray<{
  value: ClientRhymeMode;
  label: string;
  description: string;
}> = [
  {
    value: "perfect",
    label: "Perfect",
    description: "Exact rhymes from the end of the last word.",
  },
  {
    value: "near",
    label: "Near",
    description: "Looser matches — slant rhymes and assonance.",
  },
];

const STORAGE_KEY = "sa.rhymeMode";

function parseMode(raw: string | null): ClientRhymeMode {
  return raw === "perfect" || raw === "near" ? raw : DEFAULT_RHYME_MODE;
}

export function readStoredRhymeMode(): ClientRhymeMode {
  if (typeof window === "undefined") return DEFAULT_RHYME_MODE;
  return parseMode(window.localStorage.getItem(STORAGE_KEY));
}

export function writeStoredRhymeMode(mode: ClientRhymeMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, mode);
  // Notify same-tab subscribers — the storage event only fires cross-tab.
  window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY }));
}

export function subscribeToRhymeMode(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  const handler = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY || event.key === null) callback();
  };
  window.addEventListener("storage", handler);
  return () => window.removeEventListener("storage", handler);
}

export const RHYME_MODE_STORAGE_KEY = STORAGE_KEY;
