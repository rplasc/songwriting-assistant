import { apiBaseUrl } from "@/lib/config";
import type { Language } from "@/features/language/language-types";
import type { Draft, ServerDraftPayload } from "./drafts-types";
import { languageFromServer } from "./draft-language-mappers";

export class DraftRequestError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "DraftRequestError";
  }
}

interface DraftEnvelope {
  data: ServerDraftPayload;
}

function fromServer(p: ServerDraftPayload): Draft {
  return {
    id: p.id,
    title: p.title,
    content: p.content,
    language: languageFromServer(p),
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

async function parseEnvelope(response: Response): Promise<Draft> {
  if (!response.ok) {
    throw new DraftRequestError(
      `Draft request failed (${response.status})`,
      response.status,
    );
  }
  const body = (await response.json()) as DraftEnvelope;
  return fromServer(body.data);
}

export interface CreateDraftInput {
  title?: string;
  content: string;
  language: Language;
}

export interface UpdateDraftInput {
  title?: string;
  content?: string;
  language?: Language;
}

export interface DraftRequestOptions {
  signal?: AbortSignal;
}

export async function createDraft(
  input: CreateDraftInput,
  options: DraftRequestOptions = {},
): Promise<Draft> {
  const response = await fetch(`${apiBaseUrl}/v1/drafts`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    signal: options.signal,
  });
  return parseEnvelope(response);
}

export async function getDraft(
  id: string,
  options: DraftRequestOptions = {},
): Promise<Draft> {
  const response = await fetch(`${apiBaseUrl}/v1/drafts/${id}`, {
    signal: options.signal,
  });
  return parseEnvelope(response);
}

export async function updateDraft(
  id: string,
  patch: UpdateDraftInput,
  options: DraftRequestOptions = {},
): Promise<Draft> {
  const response = await fetch(`${apiBaseUrl}/v1/drafts/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(patch),
    signal: options.signal,
  });
  return parseEnvelope(response);
}
