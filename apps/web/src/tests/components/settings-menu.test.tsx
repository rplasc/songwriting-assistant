import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SettingsMenu } from "@/components/editor/settings-menu";

function setup(overrides: Partial<React.ComponentProps<typeof SettingsMenu>> = {}) {
  const onThemeChange = vi.fn();
  const onRhymeHighlightsChange = vi.fn();
  render(
    <SettingsMenu
      language="en"
      theme="system"
      onThemeChange={onThemeChange}
      rhymeHighlights={true}
      onRhymeHighlightsChange={onRhymeHighlightsChange}
      {...overrides}
    />,
  );
  return { onThemeChange, onRhymeHighlightsChange };
}

describe("SettingsMenu", () => {
  it("opens on click and marks the active theme", async () => {
    const user = userEvent.setup();
    setup({ theme: "dark" });

    await user.click(screen.getByRole("button", { name: /settings/i }));

    const dark = screen.getByRole("radio", { name: /dark/i });
    expect(dark).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: /system/i })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("emits the chosen theme", async () => {
    const user = userEvent.setup();
    const { onThemeChange } = setup();

    await user.click(screen.getByRole("button", { name: /settings/i }));
    await user.click(screen.getByRole("radio", { name: /light/i }));

    expect(onThemeChange).toHaveBeenCalledWith("light");
  });

  it("toggles rhyme highlights via the switch", async () => {
    const user = userEvent.setup();
    const { onRhymeHighlightsChange } = setup({ rhymeHighlights: true });

    await user.click(screen.getByRole("button", { name: /settings/i }));
    const sw = screen.getByRole("switch");
    expect(sw).toHaveAttribute("aria-checked", "true");

    await user.click(sw);
    expect(onRhymeHighlightsChange).toHaveBeenCalledWith(false);
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    setup();

    await user.click(screen.getByRole("button", { name: /settings/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("speaks Spanish when the draft does", async () => {
    const user = userEvent.setup();
    setup({ language: "es" });

    await user.click(screen.getByRole("button", { name: /ajustes/i }));
    expect(screen.getByText(/apariencia/i)).toBeInTheDocument();
    expect(screen.getByText(/resaltar rimas/i)).toBeInTheDocument();
  });
});
