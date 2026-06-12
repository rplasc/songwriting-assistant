import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDraftAnalysis } from "@/features/draft-analysis/use-draft-analysis";

const SAMPLE_CONTENT = "verse one line\nverse one again\n\nchorus singing now\nchorus singing now";

const originalFetch = global.fetch;

function makeAnalysisResponse(
  opts: { draftId?: string; hash?: string; status?: string } = {},
) {
  return new Response(
    JSON.stringify({
      draft_id: opts.draftId ?? "d1",
      revision_hash: opts.hash ?? "h1",
      analysis_status: opts.status ?? "fresh",
      analyzed_at: "2026-05-20T12:00:00Z",
      analysis: {
        language: "en",
        title: null,
        summary: {
          section_count: 2,
          line_count: 4,
          total_syllables: 16,
          notable_patterns: [],
        },
        insights: [],
        capabilities: {
          rhyme_scheme: "full",
          cadence_patterns: "full",
          stress_hints: "partial",
          repetition: "full",
          mixed_language: "partial",
        },
      },
      meta: { latency_ms: 12 },
    }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
}

beforeEach(() => {
  // No-op
});

afterEach(() => {
  global.fetch = originalFetch;
});

describe("useDraftAnalysis", () => {
  it("stays idle when content is too short and no draft is open", () => {
    const fetchMock = vi.fn();
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: null,
        content: "",
        language: "en",
      }),
    );
    expect(result.current.status).toBe("idle");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("auto-fires once when a draft opens with enough content", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: "d1",
        content: SAMPLE_CONTENT,
        language: "en",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(result.current.analyzedContent).toBe(SAMPLE_CONTENT);
  });

  it("transitions fresh → stale when content changes after analysis", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result, rerender } = renderHook(
      ({ content }) =>
        useDraftAnalysis({
          draftId: "d1",
          content,
          language: "en",
        }),
      { initialProps: { content: SAMPLE_CONTENT } },
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));

    rerender({ content: `${SAMPLE_CONTENT}\nnew line added later` });
    await waitFor(() => expect(result.current.status).toBe("stale"));
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("clears prior analysis when all content is deleted", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result, rerender } = renderHook(
      ({ content }) =>
        useDraftAnalysis({
          draftId: "d1",
          content,
          language: "en",
        }),
      { initialProps: { content: SAMPLE_CONTENT } },
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(result.current.analysis).not.toBeNull();

    rerender({ content: "" });

    await waitFor(() => expect(result.current.status).toBe("idle"));
    expect(result.current.analysis).toBeNull();
    expect(result.current.analyzedContent).toBeNull();
  });

  it("clears prior analysis when content falls below the analysis gate", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result, rerender } = renderHook(
      ({ content }) =>
        useDraftAnalysis({
          draftId: "d1",
          content,
          language: "en",
        }),
      { initialProps: { content: SAMPLE_CONTENT } },
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(result.current.analysis).not.toBeNull();

    rerender({ content: "short" });

    await waitFor(() => expect(result.current.status).toBe("idle"));
    expect(result.current.analysis).toBeNull();
    expect(result.current.analyzedContent).toBeNull();

    rerender({ content: `${SAMPLE_CONTENT}\nrewritten` });
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("clears prior analysis when the draft id changes", async () => {
    let resolveSecondFetch: ((response: Response) => void) | null = null;
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(makeAnalysisResponse({ draftId: "d1", hash: "h1" }))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveSecondFetch = resolve;
          }),
      );
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result, rerender } = renderHook(
      ({ draftId }) =>
        useDraftAnalysis({
          draftId,
          content: SAMPLE_CONTENT,
          language: "en",
        }),
      { initialProps: { draftId: "d1" } },
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(result.current.analysis?.draftId).toBe("d1");

    rerender({ draftId: "d2" });

    await waitFor(() => expect(result.current.status).toBe("loading"));
    expect(result.current.analysis).toBeNull();
    expect(result.current.analyzedContent).toBeNull();

    await act(async () => {
      resolveSecondFetch?.(makeAnalysisResponse({ draftId: "d2", hash: "h2" }));
    });
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    expect(result.current.analysis?.draftId).toBe("d2");
  });

  it("flags unsupported status when the server reports it", async () => {
    const fetchMock = vi.fn(async () =>
      makeAnalysisResponse({ status: "unsupported" }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: "d2",
        content: SAMPLE_CONTENT,
        language: "en",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("unsupported"));
  });

  it("reports error status when the request fails", async () => {
    global.fetch = vi.fn(
      async () => new Response("nope", { status: 500 }),
    ) as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: "d3",
        content: SAMPLE_CONTENT,
        language: "en",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current.error).toBeTruthy();
  });

  it("manual refresh re-runs the request even after stale", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: "d4",
        content: SAMPLE_CONTENT,
        language: "en",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    await act(async () => {
      await result.current.refresh();
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(result.current.status).toBe("fresh");
  });

  it("manual refresh asks the server for a non-cached analysis", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: "d5",
        content: SAMPLE_CONTENT,
        language: "en",
      }),
    );
    await waitFor(() => expect(result.current.status).toBe("fresh"));
    await act(async () => {
      await result.current.refresh();
    });
    const lastBody = JSON.parse(
      (fetchMock.mock.calls.at(-1)![1] as RequestInit).body as string,
    );
    expect(lastBody.forceRefresh).toBe(true);
  });

  it("analyzeNow runs immediately without busting the server cache", async () => {
    const fetchMock = vi.fn(async () => makeAnalysisResponse());
    global.fetch = fetchMock as unknown as typeof fetch;
    // No draftId and short content: analyzeNow must bypass the min-content
    // gate (a paste can land in a brand-new unsaved draft).
    const { result } = renderHook(() =>
      useDraftAnalysis({
        draftId: null,
        content: "two\nlines",
        language: "en",
      }),
    );
    expect(result.current.status).toBe("idle");
    await act(async () => {
      await result.current.analyzeNow();
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const body = JSON.parse(
      (fetchMock.mock.calls[0][1] as RequestInit).body as string,
    );
    expect(body.forceRefresh).toBeUndefined();
    await waitFor(() => expect(result.current.status).toBe("fresh"));
  });
});
