import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RhymeModeToggle } from "@/components/editor/rhyme-mode-toggle";

describe("RhymeModeToggle", () => {
  it("marks the active option as checked", () => {
    render(<RhymeModeToggle value="perfect" onChange={() => {}} />);
    expect(screen.getByRole("radio", { name: /perfect/i })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("radio", { name: /near/i })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("calls onChange when a different option is clicked", async () => {
    const onChange = vi.fn();
    render(<RhymeModeToggle value="perfect" onChange={onChange} />);
    await userEvent.click(screen.getByRole("radio", { name: /near/i }));
    expect(onChange).toHaveBeenCalledWith("near");
  });
});
