import type { ReactNode } from "react";
import ResearchGlyph, {
  type ResearchGlyphName,
} from "@/components/features/research/ResearchGlyph";

export type ResearchBandProps = {
  caption: string;
  glyph?: ResearchGlyphName;
  children: ReactNode;
  /** When true, omit bottom padding reduction used on action bands. */
  action?: boolean;
  className?: string;
};

/**
 * Shared lifecycle section band: caption (+ optional glyph) then content.
 */
export default function ResearchBand({
  caption,
  glyph,
  children,
  action = false,
  className = "",
}: ResearchBandProps) {
  return (
    <section
      className={`research-band${action ? " research-band--action" : ""}${
        className ? ` ${className}` : ""
      }`}
      aria-label={caption}
    >
      <p className="overview-caption">
        {glyph ? <ResearchGlyph name={glyph} /> : null}
        <span>{caption}</span>
      </p>
      {children}
    </section>
  );
}
