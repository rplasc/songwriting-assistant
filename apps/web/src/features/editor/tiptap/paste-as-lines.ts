import { Extension } from "@tiptap/core";
import { Fragment, Slice } from "@tiptap/pm/model";
import { Plugin } from "@tiptap/pm/state";

/**
 * Transaction meta flag set on multi-line pastes. The editor shell watches
 * for it to kick off a draft analysis right away, so pasted lines get their
 * margin syllable counts without waiting for the stale-idle refresh.
 */
export const PASTE_AS_LINES_META = "pasteAsLines";

/**
 * Split clipboard text into one entry per lyric line. A single trailing
 * newline is dropped so a copied block doesn't leave a stray blank line.
 * Exported for unit tests.
 */
export function splitPastedLines(text: string): string[] {
  return text.replace(/\r\n?/g, "\n").replace(/\n$/, "").split("\n");
}

/**
 * Without this, pasting multi-line plain text lands inside a single
 * paragraph as hardBreak-separated content — one "line" as far as the
 * analysis/decoration layers are concerned. Each pasted line should become
 * its own paragraph, matching the editor's one-paragraph-per-lyric-line
 * contract (see editor-lines.ts).
 */
export const PasteAsLines = Extension.create({
  name: "pasteAsLines",

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handlePaste: (view, event) => {
            const text = event.clipboardData?.getData("text/plain");
            if (!text || !text.includes("\n")) return false;

            const { schema } = view.state;
            const paragraph = schema.nodes.paragraph;
            if (!paragraph) return false;

            const nodes = splitPastedLines(text).map((line) =>
              line
                ? paragraph.create(null, schema.text(line))
                : paragraph.create(null),
            );
            const slice = new Slice(Fragment.fromArray(nodes), 1, 1);
            view.dispatch(
              view.state.tr
                .replaceSelection(slice)
                .setMeta(PASTE_AS_LINES_META, true),
            );
            return true;
          },
        },
      }),
    ];
  },
});
