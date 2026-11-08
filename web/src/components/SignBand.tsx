import type { ReactNode } from "react";

/**
 * A black signage band with white type: how the map names a section, like a platform sign.
 *
 * By default the band bleeds out to the page gutter, so its text lines up with the content
 * under it. `bleed={false}` keeps it inside its box, for a band that heads a panel which itself
 * bleeds or stands alone; its text is inset by the same gutter.
 * `split` sets the title and the band's other text in the two columns of the hero above it.
 */
export function SignBand({
  title,
  id,
  children,
  as: Heading = "h2",
  bleed = true,
  split = false,
}: {
  title: ReactNode;
  id?: string;
  children?: ReactNode;
  as?: "h1" | "h2" | "h3";
  bleed?: boolean;
  split?: boolean;
}) {
  const edges = bleed ? "-mx-5 px-5 sm:-mx-8 sm:px-8" : "px-5 sm:px-8";
  const layout = split
    ? "grid gap-x-12 gap-y-1.5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-baseline"
    : "flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1.5";
  return (
    <div className={`${layout} ${edges} bg-band py-3.5 text-white`}>
      <Heading id={id} className="text-xl font-bold tracking-[-0.01em] sm:text-2xl">
        {title}
      </Heading>
      {children ? <div className={split ? "" : "sm:text-right"}>{children}</div> : null}
    </div>
  );
}
