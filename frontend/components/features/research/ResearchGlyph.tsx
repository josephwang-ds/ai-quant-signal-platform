/** Lightweight scan glyphs — decorative only, always aria-hidden by parent. */

export type ResearchGlyphName =
  | "decision"
  | "action"
  | "progress"
  | "evidence"
  | "workflow"
  | "support"
  | "blocker"
  | "limitation";

type Props = {
  name: ResearchGlyphName;
  className?: string;
};

export default function ResearchGlyph({ name, className = "research-glyph" }: Props) {
  const common = {
    className,
    width: 14,
    height: 14,
    viewBox: "0 0 16 16",
    fill: "none",
    "aria-hidden": true as const,
  };

  switch (name) {
    case "decision":
      return (
        <svg {...common}>
          <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 4.5v4l2.5 1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "action":
      return (
        <svg {...common}>
          <path
            d="M3 8h10M9 4l4 4-4 4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "progress":
      return (
        <svg {...common}>
          <path
            d="M2 12V4h3.5l1.5 2H14v6H2z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "evidence":
      return (
        <svg {...common}>
          <path
            d="M4 2.5h6l2.5 2.5V13.5H4V2.5z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <path d="M6 8h4M6 10.5h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "workflow":
      return (
        <svg {...common}>
          <circle cx="3.5" cy="8" r="1.5" fill="currentColor" />
          <circle cx="8" cy="8" r="1.5" fill="currentColor" />
          <circle cx="12.5" cy="8" r="1.5" fill="currentColor" />
          <path d="M5 8h1.5M9.5 8H11" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      );
    case "support":
      return (
        <svg {...common}>
          <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 5v3.5M8 11h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "blocker":
      return (
        <svg {...common}>
          <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
          <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "limitation":
      return (
        <svg {...common}>
          <path
            d="M8 2.5 13.5 13H2.5L8 2.5z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <path d="M8 7v2.5M8 11.5h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
  }
}
