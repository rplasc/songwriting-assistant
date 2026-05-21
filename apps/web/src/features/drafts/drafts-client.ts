import { apiBaseUrl } from "@/lib/config";
import type { Language } from "@/features/language/language-types";
import {
  sectionFromServer,
  type DraftSection,
} from "@/features/structure/structure-types";
import type { Draft, ServerDraftPayload } from "./drafts-types";
import { languageFromServer } from "./draft-language-mappers";

export interface DraftSectionInput {
  label: string;
  lineStart: number;
  lineEnd: number;
}

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
    sections: (p.sections ?? []).map(sectionFromServer),
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

function toSectionInput(s: DraftSection): DraftSectionInput {
  return { label: s.label, lineStart: s.lineStart, lineEnd: s.lineEnd };
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
  sections?: DraftSection[];
}

export interface UpdateDraftInput {
  title?: string;
  content?: string;
  language?: Language;
  sections?: DraftSection[];
}

export interface DraftRequestOptions {
  signal?: AbortSignal;
}

export async function createDraft(
  input: CreateDraftInput,
  options: DraftRequestOptions = {},
): Promise<Draft> {
  const body: Record<string, unknown> = {
    content: input.content,
    language: input.language,
  };
  if (input.title !== undefined) body.title = input.title;
  if (input.sections !== undefined) body.sections = input.sections.map(toSectionInput);
  const response = await fetch(`${apiBaseUrl}/v1/drafts`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
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

export async function deleteDraft(
  id: string,
  options: DraftRequestOptions = {},
): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/v1/drafts/${id}`, {
    method: "DELETE",
    signal: options.signal,
  });
  if (!response.ok && response.status !== 404) {
    throw new DraftRequestError(
      `Draft delete failed (${response.status})`,
      response.status,
    );
  }
}

export async function updateDraft(
  id: string,
  patch: UpdateDraftInput,
  options: DraftRequestOptions = {},
): Promise<Draft> {
  const body: Record<string, unknown> = {};
  if (patch.title !== undefined) body.title = patch.title;
  if (patch.content !== undefined) body.content = patch.content;
  if (patch.language !== undefined) body.language = patch.language;
  if (patch.sections !== undefined) body.sections = patch.sections.map(toSectionInput);
  const response = await fetch(`${apiBaseUrl}/v1/drafts/${id}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  return parseEnvelope(response);
}
