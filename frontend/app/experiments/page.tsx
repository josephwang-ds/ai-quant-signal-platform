import { permanentRedirect } from "next/navigation";

/**
 * Experiments is no longer a top-level product surface.
 * Cost / saved-run / robustness work belongs under Backtesting.
 */
export default function ExperimentsRedirectPage() {
  permanentRedirect("/engine/backtest");
}
