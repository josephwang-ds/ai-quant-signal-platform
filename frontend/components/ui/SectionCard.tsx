import type { ReactNode } from "react";

type SectionCardProps = {
  id?: string;
  children: ReactNode;
  compact?: boolean;
  error?: boolean;
  className?: string;
};

export default function SectionCard({
  id,
  children,
  compact = false,
  error = false,
  className = "",
}: SectionCardProps) {
  const classes = [
    "section-card",
    compact ? "section-card--compact" : "",
    error ? "section-card--error" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section id={id} className={classes}>
      {children}
    </section>
  );
}
