import { Language } from '../common/enums/language.enum';

export interface Draft {
  id: string;
  title: string;
  content: string;
  language: Language;
  createdAt: string;
  updatedAt: string;
}
