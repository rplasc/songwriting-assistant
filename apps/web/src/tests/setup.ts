import "@testing-library/jest-dom";

// Vitest 4 + jsdom 29 + Node 22's experimental --localstorage-file flag together
// produce a window.localStorage that throws on most operations. Replace it with
// a deterministic in-memory polyfill for tests.
function installMemoryStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key) {
      return store.has(key) ? (store.get(key) as string) : null;
    },
    key(index) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key) {
      store.delete(key);
    },
    setItem(key, value) {
      store.set(String(key), String(value));
    },
  };
}

Object.defineProperty(window, "localStorage", {
  configurable: true,
  value: installMemoryStorage(),
});
