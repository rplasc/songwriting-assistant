"use client";

import { useEditor, type Editor } from "@tiptap/react";
import { useEffect, useState } from "react";
import { lyricEditorExtensions } from "./editor-extensions";

export interface LyricEditorState {
  editor: Editor | null;
  activeLine: string;
}

function readActiveLine(editor: Editor): string {
  const { $from } = editor.state.selection;
  // The cursor's nearest block (paragraph) — treat each paragraph as one lyric line.
  const block = $from.node($from.depth);
  return (block?.textContent ?? "").trim();
}

export function useLyricEditor(): LyricEditorState {
  const [activeLine, setActiveLine] = useState<string>("");

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
    },
  });

  useEffect(() => {
    if (editor) setActiveLine(readActiveLine(editor));
  }, [editor]);

  return { editor, activeLine };
}
