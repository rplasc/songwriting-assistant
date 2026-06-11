import { LyricEditorShell } from "@/components/editor/lyric-editor-shell";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-4 py-8 sm:px-6 sm:py-12 2xl:px-12 2xl:py-16">
      <div className="w-full max-w-7xl 2xl:max-w-440">
        <header className="mb-6 flex flex-col items-center text-center sm:mb-8">
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Songwriting Tool Demo
          </h1>
        </header>
        <LyricEditorShell />
      </div>
    </main>
  );
}
