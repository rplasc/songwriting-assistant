import { LyricEditorShell } from "@/components/editor/lyric-editor-shell";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-4 py-10 sm:px-10 sm:py-16 2xl:px-20 2xl:py-20">
      <div className="flex w-full max-w-6xl flex-col gap-10 2xl:max-w-432 2xl:gap-14">
        <header className="flex flex-col gap-3">
          <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl 2xl:text-5xl">
            Songwriting Assistant
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base 2xl:max-w-2xl 2xl:text-base">
            Write. I&rsquo;ll count syllables and find rhymes as you go.
          </p>
          <hr className="mt-1 border-border" />
        </header>

        <LyricEditorShell />
      </div>
    </main>
  );
}
