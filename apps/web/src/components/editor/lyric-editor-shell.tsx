"use client";

import { useEditorAnalysis } from "@/features/analysis/use-editor-analysis";
import { useLyricEditor } from "@/features/editor/tiptap/use-lyric-editor";
import { cn } from "@/lib/utils";
import { EditorLayout } from "./editor-layout";
import { LyricEditor } from "./lyric-editor";
import { RhymePanel } from "./rhyme-panel";
import { SyllablePanel } from "./syllable-panel";

export function LyricEditorShell() {
  const { editor, activeLine } = useLyricEditor();
  const { result, status, error } = useEditorAnalysis(activeLine);

  return (
    <div className="flex flex-col gap-2">
      <EditorLayout
        editor={<LyricEditor editor={editor} />}
        panels={
          <>
            <SyllablePanel status={status} result={result} />
            <RhymePanel status={status} result={result} />
          </>
        }
      />
      {status === "error" && error ? (
        <div
          role="alert"
          className="mt-1 rounded border border-border bg-surface-muted px-3 py-2 text-[11px] text-muted-foreground"
        >
          {error} Keep writing — analysis will retry automatically.
        </div>
      ) : null}
    </div>
  );
}
