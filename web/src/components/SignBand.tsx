import type { ReactNode } from "react";

/** A black signage band with white type: how the map names a section, like a platform sign. */
export function SignBand({
  title,
  id,
  children,
  as: Heading = "h2",
}: {
  title: ReactNode;
  id?: string;
  children?: ReactNode;
  as?: "h1" | "h2" | "h3";
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 bg-band px-5 py-3.5 text-white sm:px-6">
      <Heading id={id} className="text-xl font-bold tracking-[-0.01em] sm:text-2xl">
        {title}
      </Heading>
      {children}
    </div>
  );
}
