import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEditorAnalysis } from "@/features/analysis/use-editor-analysis";
import type {
  EmitAnalyzeOptions,
  SocketAnalysisAdapter,
} from "@/features/analysis/analysis-socket";
import type { ServerAnalysisPayload } from "@/features/analysis/analysis-types";

const emit = vi.fn<(options: EmitAnalyzeOptions) => void>();
let analysisHandler: ((payload: ServerAnalysisPayload) => void) | null = null;

vi.mock("@/features/analysis/analysis-socket", () => ({
  getSocketAdapter: (): SocketAnalysisAdapter => ({
    emit,
    onAnalysis: (handler) => {
      analysisHandler = handler;
      return () => {
        analysisHandler = null;
      };
    },
    onError: () => () => {},
    onConnectError: () => () => {},
    isConnected: () => true,
  }),
}));

function makePayload(
  overrides: Partial<ServerAnalysisPayload> = {},
): ServerAnalysisPayload {
  return {
    line: "hello world",
    language: "en",
    syllables: { total: 3, tokens: [] },
    rhymes: { target_word: "world", mode: "perfect", items: [] },
    inner_rhymes: [],
    meta: { latency_ms: 5 },
    ...overrides,
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  emit.mockClear();
  analysisHandler = null;
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useEditorAnalysis", () => {
  it("does not re-send an identical request once the result is ready", () => {
    const { result, rerender } = renderHook(
      ({ word }: { word: string | null }) =>
        useEditorAnalysis("hello world", word, "perfect", "en"),
      { initialProps: { word: "world" as string | null } },
    );

    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(emit).toHaveBeenCalledTimes(1);

    act(() => {
      analysisHandler?.(makePayload());
    });
    expect(result.current.status).toBe("ready");

    // Deps change away and back to the same value before the debounce for
    // the intermediate render fires — the pending request is never sent,
    // so `latestSentRef` still reflects the original (now-ready) request.
    rerender({ word: null });
    rerender({ word: "world" });

    act(() => {
      vi.advanceTimersByTime(150);
    });

    // The ready result already matches these params — no duplicate send.
    expect(emit).toHaveBeenCalledTimes(1);
  });

  it("re-sends when skipRhymes toggles even for the same line and word", () => {
    const { rerender } = renderHook(
      ({ skipRhymes }: { skipRhymes: boolean }) =>
        useEditorAnalysis("hello world", "world", "perfect", "en", skipRhymes),
      { initialProps: { skipRhymes: false } },
    );

    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(emit).toHaveBeenCalledTimes(1);
    expect(emit).toHaveBeenLastCalledWith(
      expect.objectContaining({ skipRhymes: false }),
    );

    act(() => {
      analysisHandler?.(makePayload());
    });

    rerender({ skipRhymes: true });
    act(() => {
      vi.advanceTimersByTime(150);
    });

    expect(emit).toHaveBeenCalledTimes(2);
    expect(emit).toHaveBeenLastCalledWith(
      expect.objectContaining({ skipRhymes: true }),
    );
  });
});
