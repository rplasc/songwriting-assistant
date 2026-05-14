import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { debounce } from "@/features/analysis/debounce";

describe("debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not call fn immediately", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 200);
    debouncedFn();
    expect(fn).not.toHaveBeenCalled();
  });

  it("calls fn after the delay", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 200);
    debouncedFn();
    vi.advanceTimersByTime(200);
    expect(fn).toHaveBeenCalledOnce();
  });

  it("resets the timer on repeated calls within the delay window", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 200);
    debouncedFn("a");
    vi.advanceTimersByTime(100);
    debouncedFn("b");
    vi.advanceTimersByTime(100);
    expect(fn).not.toHaveBeenCalled();
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledOnce();
    expect(fn).toHaveBeenCalledWith("b");
  });

  it("cancel() prevents the pending call", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 200);
    debouncedFn();
    debouncedFn.cancel();
    vi.advanceTimersByTime(300);
    expect(fn).not.toHaveBeenCalled();
  });

  it("passes arguments correctly", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 100);
    debouncedFn("foo", 42);
    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledWith("foo", 42);
  });
});
