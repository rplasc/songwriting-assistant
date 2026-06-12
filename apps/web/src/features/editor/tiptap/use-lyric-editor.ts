"use client";

import { useEditor, type Editor } from "@tiptap/react";
import { useEffect, useState } from "react";
import { extractWordAt } from "@/features/analysis/active-line";
import { lyricEditorExtensions } from "./editor-extensions";
import { getEditorText } from "./editor-lines";
import { lineAtSelection } from "./line-descriptors";

export interface LyricEditorState {
  editor: Editor | null;
  activeLine: string;
  /** The word the caret is on (or just typed) — the rhyme target. */
  activeWord: string | null;
  /** 1-based paragraph number of the caret line. */
  activeLineNumber: number;
  content: string;
}

function readActiveLine(editor: Editor): string {
  const { $from } = editor.state.selection;
  // The cursor's nearest block (paragraph) — treat each paragraph as one lyric line.
  const block = $from.node($from.depth);
  return (block?.textContent ?? "").trim();
}

function readActiveWord(editor: Editor): string | null {
  const { $from } = editor.state.selection;
  const block = $from.node($from.depth);
  // parentOffset is the caret's character offset inside the paragraph text.
  return extractWordAt(block?.textContent ?? "", $from.parentOffset);
}

export function useLyricEditor(): LyricEditorState {
  const [activeLine, setActiveLine] = useState<string>("");
  const [activeWord, setActiveWord] = useState<string | null>(null);
  const [activeLineNumber, setActiveLineNumber] = useState<number>(1);
  const [content, setContent] = useState<string>("");

  const editor = useEditor({
    extensions: lyricEditorExtensions,
    content: "",
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: "tiptap",
        "aria-label": "Lyric editor",
        spellcheck: "false",
        autocorrect: "off",
        autocapitalize: "off",
      },
    },
    onTransaction({ editor: instance }) {
      setActiveLine(readActiveLine(instance));
      setActiveWord(readActiveWord(instance));
      setActiveLineNumber(lineAtSelection(instance.state));
    },
    onUpdate({ editor: instance }) {
      setContent(getEditorText(instance));
    },
    onCreate({ editor: instance }) {
      setContent(getEditorText(instance));
    },
  });

  useEffect(() => {
    if (editor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- seeding state from the editor instance when it mounts
      setActiveLine(readActiveLine(editor));
      setActiveWord(readActiveWord(editor));
      setActiveLineNumber(lineAtSelection(editor.state));
      setContent(getEditorText(editor));
    }
  }, [editor]);

  return { editor, activeLine, activeWord, activeLineNumber, content };
}
