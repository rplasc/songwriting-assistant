import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EditorStatusStrip } from "@/components/editor/editor-status-strip";

describe("EditorStatusStrip", () => {
  it("reflects an open rail and underline count", () => {
    render(
      <EditorStatusStrip
        railOpen={true}
        rhymeGroupCount={4}
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
        offline={true}
        language="en"
      />,
    );
    const strip = screen.getByText(/rail closed/i);
    expect(strip).toHaveTextContent(/offline/i);
  });

  it("speaks Spanish when the draft does", () => {
    render(
      <EditorStatusStrip
        railOpen={true}
        rhymeGroupCount={1}
        offline={false}
        language="es"
      />,
    );
    expect(screen.getByText(/margen abierto/i)).toBeInTheDocument();
  });
});
