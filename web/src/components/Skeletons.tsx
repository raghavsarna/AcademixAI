function Block({ className }: { className: string }) {
  return <div className={`rounded-[3px] bg-panel motion-safe:animate-pulse ${className}`} />;
}

export function EditionSkeleton() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-14 sm:px-8" aria-busy="true" aria-label="Loading the edition">
      <Block className="h-14 max-w-3xl" />
      <Block className="mt-3 h-14 max-w-xl" />
      <Block className="mt-6 h-5 max-w-md" />
      <Block className="mt-6 h-20 max-w-[60ch]" />
      <div className="mt-12 grid gap-6 lg:grid-cols-[2.1fr_1fr]">
        <Block className="h-80" />
        <Block className="h-80" />
      </div>
    </div>
  );
}

export function PaperSkeleton() {
  return (
    <div className="mx-auto max-w-[88rem] px-5 pt-14 sm:px-8" aria-busy="true" aria-label="Loading the paper">
      <Block className="h-6 w-40" />
      <Block className="mt-5 h-12 max-w-3xl" />
      <Block className="mt-3 h-12 max-w-2xl" />
      <Block className="mt-8 h-32 max-w-[60ch]" />
      <Block className="mt-10 h-72 max-w-[60ch]" />
    </div>
  );
}

export function ListSkeleton() {
  return (
    <div className="grid gap-3" aria-busy="true" aria-label="Loading">
      {Array.from({ length: 5 }, (_, i) => (
        <Block key={i} className="h-16" />
      ))}
    </div>
  );
}
