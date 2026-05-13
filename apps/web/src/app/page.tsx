import { LyricEditorShell } from "@/components/editor/lyric-editor-shell";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-4 py-10 sm:px-8 sm:py-14">
      <div className="flex w-full max-w-6xl flex-col gap-8">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Songwriting Assistant
          </h1>
          <p className="max-w-2xl text-sm text-muted-foreground sm:text-base">
            Type a line, pause, and the active line gets syllable counts and rhyme suggestions automatically.
          </p>
        </header>
        <LyricEditorShell />
      </div>
    </main>
  );
}
