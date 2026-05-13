import { apiBaseUrl } from "@/lib/config";
import type { ServerAnalysisPayload } from "./analysis-types";

export class AnalysisRequestError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "AnalysisRequestError";
  }
}

export interface AnalyzeLineOptions {
  signal?: AbortSignal;
}

export async function analyzeLine(
  line: string,
  options: AnalyzeLineOptions = {},
): Promise<ServerAnalysisPayload> {
  const response = await fetch(`${apiBaseUrl}/v1/editor/analyze`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ line }),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new AnalysisRequestError(
      `Analyze request failed (${response.status})`,
      response.status,
    );
  }

  return (await response.json()) as ServerAnalysisPayload;
}
