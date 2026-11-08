"use client";

import { useCallback, useEffect, useLayoutEffect, useRef } from "react";

import { DEPTH_LABELS, DEPTHS, type Depth } from "@/lib/types";

/** Plain / Student / Expert segmented control (transitions.dev tabs sliding). */
export function DepthSwitch({
  value,
  onChange,
  label = "Reading depth",
  controls,
}: {
  value: Depth;
  onChange: (depth: Depth) => void;
  label?: string;
  controls?: string;
}) {
  const bar = useRef<HTMLDivElement>(null);
  const pill = useRef<HTMLSpanElement>(null);
  const animate = useRef(false);

  const moveTo = useCallback((tab: HTMLElement, withTransition: boolean) => {
    const p = pill.current;
    if (!p) return;
    if (!withTransition) {
      const previous = p.style.transition;
      p.style.transition = "none";
      p.style.transform = `translateX(${tab.offsetLeft}px)`;
      p.style.width = `${tab.offsetWidth}px`;
      void p.offsetWidth;
      p.style.transition = previous;
    } else {
      p.style.transform = `translateX(${tab.offsetLeft}px)`;
      p.style.width = `${tab.offsetWidth}px`;
    }
  }, []);

  useLayoutEffect(() => {
    const tab = bar.current?.querySelector<HTMLElement>(`[data-depth="${value}"]`);
    if (tab) moveTo(tab, animate.current);
    animate.current = true;
  }, [value, moveTo]);

  useEffect(() => {
    const onResize = () => {
      const tab = bar.current?.querySelector<HTMLElement>('[aria-selected="true"]');
      if (tab) moveTo(tab, false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [moveTo]);

  const onKeyDown = (event: React.KeyboardEvent) => {
    const index = DEPTHS.indexOf(value);
    const next =
      event.key === "ArrowRight" ? DEPTHS[(index + 1) % 3] : event.key === "ArrowLeft" ? DEPTHS[(index + 2) % 3] : null;
    if (!next) return;
    event.preventDefault();
    onChange(next);
    bar.current?.querySelector<HTMLElement>(`[data-depth="${next}"]`)?.focus();
  };

  return (
    <div ref={bar} className="t-tabs depth-switch" role="tablist" aria-label={label} onKeyDown={onKeyDown}>
      <span ref={pill} className="t-tabs-pill" aria-hidden="true" />
      {DEPTHS.map((depth) => (
        <button
          key={depth}
          type="button"
          role="tab"
          className="t-tab"
          data-depth={depth}
          aria-selected={depth === value}
          aria-controls={controls}
          tabIndex={depth === value ? 0 : -1}
          onClick={() => onChange(depth)}
        >
          {DEPTH_LABELS[depth]}
        </button>
      ))}
    </div>
  );
}
