/** Two research lines meeting at an interchange, the mark of the map. */
export function LogoMark({ className = "size-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden fill="none">
      <path d="M2 20 H13 L21 12 H30" stroke="var(--color-line-language)" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 30 V24 L16 16 V2" stroke="var(--color-line-vision)" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="10.5" y="13.5" width="11" height="9" rx="4.5" transform="rotate(-45 16 18)" fill="#ffffff" stroke="currentColor" strokeWidth="2.25" />
    </svg>
  );
}

export function Wordmark() {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark />
      <span className="text-[1.375rem] font-extrabold tracking-[-0.02em]">AcademixAI</span>
    </span>
  );
}
