"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect } from "react";

import { DEPTHS, type Depth } from "./types";

const KEY = "academixai.depth";

function isDepth(value: string | null): value is Depth {
  return value !== null && (DEPTHS as readonly string[]).includes(value);
}

/** The reader's depth: from ?depth= in the URL, else their last choice, else Student. */
export function useDepth(): [Depth, (depth: Depth) => void] {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const fromUrl = params.get("depth");
  const depth: Depth = isDepth(fromUrl) ? fromUrl : "student";

  const setDepth = useCallback(
    (next: Depth) => {
      try {
        window.localStorage.setItem(KEY, next);
      } catch {
        // Not remembering the choice is fine.
      }
      const query = new URLSearchParams(params.toString());
      query.set("depth", next);
      router.replace(`${pathname}?${query.toString()}` as never, { scroll: false });
    },
    [params, pathname, router],
  );

  // No depth in the URL: restore the reader's last choice.
  useEffect(() => {
    if (isDepth(fromUrl)) return;
    try {
      const saved = window.localStorage.getItem(KEY);
      if (isDepth(saved) && saved !== "student") setDepth(saved);
    } catch {
      // Storage unavailable: stay on Student.
    }
  }, [fromUrl, setDepth]);

  return [depth, setDepth];
}
