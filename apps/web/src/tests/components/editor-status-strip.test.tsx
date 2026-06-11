import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EditorStatusStrip } from "@/components/editor/editor-status-strip";

describe("EditorStatusStrip", () => {
  it("reflects an open rail and underline count", () => {
    render(
      <EditorStatusStrip
        railOpen={true}
        rhymeGroupCount={4}
        rhymeHighlights={true}
        offline={false}
        language="en"
      />,
    );
    const strip = screen.getByText(/rail open/i);
    expect(strip).toHaveTextContent(/4 rhyme groups underlined/i);
    expect(strip).toHaveTextContent(/syllables at right edge/i);
    expect(strip).not.toHaveTextContent(/offline/i);
  });

  it("reflects a closed rail and offline state", () => {
    render(
      <EditorStatusStrip
        railOpen={false}
        rhymeGroupCount={0}
        rhymeHighlights={true}
        offline={true}
        language="en"
      />,
    );
    const strip = screen.getByText(/rail closed/i);
    expect(strip).toHaveTextContent(/offline/i);
  });

  it("notes when rhyme highlights are turned off", () => {
    render(
      <EditorStatusStrip
        railOpen={true}
        rhymeGroupCount={4}
        rhymeHighlights={false}
        offline={false}
        language="en"
      />,
    );
    const strip = screen.getByText(/rail open/i);
    expect(strip).toHaveTextContent(/rhyme highlights off/i);
    expect(strip).not.toHaveTextContent(/underlined/i);
  });

  it("speaks Spanish when the draft does", () => {
    render(
      <EditorStatusStrip
        railOpen={true}
        rhymeGroupCount={1}
        rhymeHighlights={true}
        offline={false}
        language="es"
      />,
    );
    expect(screen.getByText(/margen abierto/i)).toBeInTheDocument();
  });
});
