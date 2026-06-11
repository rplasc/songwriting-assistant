import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";
import { LineMetrics } from "./line-metrics-extension";
import { SectionLabels } from "./section-label-extension";
import { InnerRhymes } from "./inner-rhyme-extension";
import { PasteAsLines } from "./paste-as-lines";

export const lyricEditorExtensions = [
  StarterKit.configure({
    heading: false,
    blockquote: false,
    code: false,
    codeBlock: false,
    horizontalRule: false,
    bulletList: false,
    orderedList: false,
    listItem: false,
    strike: false,
  }),
  Placeholder.configure({
    placeholder: "Start a line…",
  }),
  LineMetrics,
  SectionLabels,
  InnerRhymes,
  PasteAsLines,
];
