import Placeholder from "@tiptap/extension-placeholder";
import StarterKit from "@tiptap/starter-kit";

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
];
