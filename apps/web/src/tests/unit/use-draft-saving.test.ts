import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Editor } from "@tiptap/react";
import { useDraftSaving } from "@/features/drafts/use-draft-saving";

interface FakeEditor {
  text: string;
  listeners: Set<() => void>;
  on: (event: string, handler: () => void) => void;
  off: (event: string, handler: () => void) => void;
  getText: () => string;
  getHTML: () => string;
  state: { doc: FakeDoc };
  commands: { setContent: ReturnType<typeof vi.fn> };
  type: (text: string) => void;
}

interface FakeDoc {
  readonly textContent: string;
  forEach: (fn: (node: { textContent: string }) => void) => void;
}

function createFakeEditor(): FakeEditor {
  const listeners = new Set<() => void>();
  const editor: FakeEditor = {
    text: "",
    listeners,
    on(event, handler) {
      if (event === "update") listeners.add(handler);
    },
    off(event, handler) {
      if (event === "update") listeners.delete(handler);
    },
    getText() {
      return this.text;
    },
    getHTML() {
      return editor.text
        .split("\n")
        .map((line) => `<p>${line}</p>`)
        .join("");
    },
    // Just enough of the ProseMirror doc for getEditorText / emptiness checks.
    state: {
      doc: {
        get textContent() {
          return editor.text;
        },
        forEach(fn) {
          for (const line of editor.text.split("\n")) {
            fn({ textContent: line });
          }
        },
      },
    },
    commands: {
      setContent: vi.fn((text: string) => {
        editor.text = text;
        for (const fn of listeners) fn();
      }),
    },
    type(text) {
      this.text = text;
      for (const fn of listeners) fn();
    },
  };
  return editor;
}

const originalFetch = global.fetch;

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  global.fetch = originalFetch;
});

function makeFetchMock(): ReturnType<typeof vi.fn> {
  let counter = 0;
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url.endsWith("/v1/drafts") && method === "POST") {
      counter += 1;
      const id = `draft-${counter}`;
      const now = new Date().toISOString();
      return new Response(
        JSON.stringify({
          data: {
            id,
            title: "Untitled Draft",
            content: JSON.parse(init!.body as string).content,
            created_at: now,
            updated_at: now,
          },
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      );
    }
    if (url.includes("/v1/drafts/") && method === "PATCH") {
      const id = url.split("/").pop() ?? "draft";
      const now = new Date().toISOString();
      return new Response(
        JSON.stringify({
          data: {
            id,
            title: "Untitled Draft",
            content: JSON.parse(init!.body as string).content ?? "",
            created_at: now,
            updated_at: now,
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }
    throw new Error(`Unhandled request: ${method} ${url}`);
  });
}

describe("useDraftSaving", () => {
  it("starts idle when the editor is empty", () => {
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );
    expect(result.current.status).toBe("idle");
    expect(result.current.currentDraftId).toBeNull();
  });

  it("marks the status dirty as soon as the editor updates", () => {
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );
    act(() => {
      editor.type("Hello darkness");
    });
    expect(result.current.status).toBe("dirty");
  });

  it("creates a draft when saveNow runs for the first time", async () => {
    const fetchMock = makeFetchMock();
    global.fetch = fetchMock as unknown as typeof fetch;
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );

    act(() => editor.type("Hello darkness"));
    await act(async () => {
      await result.current.saveNow();
    });

    await waitFor(() => expect(result.current.status).toBe("saved"));
    expect(result.current.currentDraftId).toMatch(/^draft-/);
    const postCalls = fetchMock.mock.calls.filter(
      (call) => (call[1] as RequestInit | undefined)?.method === "POST",
    );
    expect(postCalls).toHaveLength(1);
  });

  it("PATCHes on subsequent saves", async () => {
    const fetchMock = makeFetchMock();
    global.fetch = fetchMock as unknown as typeof fetch;
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );

    act(() => editor.type("first"));
    await act(async () => {
      await result.current.saveNow();
    });
    await waitFor(() => expect(result.current.status).toBe("saved"));

    act(() => editor.type("first revised"));
    await act(async () => {
      await result.current.saveNow();
    });
    await waitFor(() => expect(result.current.status).toBe("saved"));

    const methods = fetchMock.mock.calls.map(
      (call) => (call[1] as RequestInit | undefined)?.method ?? "GET",
    );
    expect(methods).toContain("POST");
    expect(methods).toContain("PATCH");
  });

  it("flips to offline when the gateway is unreachable", async () => {
    // Native fetch rejects with TypeError on network failure — the hook's
    // retry classifier keys off that.
    global.fetch = vi.fn(() =>
      Promise.reject(new TypeError("network down")),
    ) as unknown as typeof fetch;
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );

    act(() => editor.type("offline test"));
    // Don't await saveNow — it stays pending through the retry backoff.
    // The hook flips to "offline" before the first backoff sleep.
    act(() => {
      void result.current.saveNow();
    });
    await waitFor(() => expect(result.current.status).toBe("offline"));
  });

  it("clears editor and id on newDraft", async () => {
    const fetchMock = makeFetchMock();
    global.fetch = fetchMock as unknown as typeof fetch;
    const editor = createFakeEditor();
    const { result } = renderHook(() =>
      useDraftSaving(editor as unknown as Editor, { language: "en" }),
    );

    act(() => editor.type("seed"));
    await act(async () => {
      await result.current.saveNow();
    });
    await waitFor(() => expect(result.current.status).toBe("saved"));

    act(() => result.current.newDraft());
    expect(result.current.status).toBe("idle");
    expect(result.current.currentDraftId).toBeNull();
    expect(editor.commands.setContent).toHaveBeenCalledWith("", true);
  });
});
