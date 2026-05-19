import { Language, RhymeMode } from '../../common/enums/language.enum';

export interface AnalyzeLineRequest {
  line: string;
  language?: Language;
}

export interface RhymesRequest {
  word: string;
  limit?: number;
  language?: Language;
  /** Field name matches the FastAPI schema. */
  mode?: RhymeMode;
}
