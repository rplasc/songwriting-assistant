"use client";

import { EditorContent, type Editor } from "@tiptap/react";
import { cn } from "@/lib/utils";
import type { RhymeHighlightStyle } from "@/features/settings/preferences";

interface LyricEditorProps {
  editor: Editor | null;
  rhymeHighlightStyle: RhymeHighlightStyle;
}

export function LyricEditor({ editor, rhymeHighlightStyle }: LyricEditorProps) {
  return (
    <div
      className={cn(
        "min-h-96 rounded-sm bg-surface px-6 py-6 shadow-[0_1px_3px_0_rgb(0,0,0,0.05),0_10px_30px_-16px_rgb(0,0,0,0.12)] transition-shadow duration-200 focus-within:shadow-[0_1px_3px_0_rgb(0,0,0,0.06),0_10px_30px_-14px_rgb(0,0,0,0.16)] sm:px-10 sm:py-8",
        rhymeHighlightStyle === "marker"
          ? "rhyme-style-marker"
          : "rhyme-style-underline",
      )}
    >
      <EditorContent editor={editor} />
    </div>
  );
}
