import { Language } from '../common/enums/language.enum';

export interface DraftSection {
  id: string;
  label: string;
  lineStart: number;
  lineEnd: number;
}

export interface Draft {
  id: string;
  title: string;
  content: string;
  language: Language;
  sections?: DraftSection[];
  version: number;
  createdAt: string;
  updatedAt: string;
}
