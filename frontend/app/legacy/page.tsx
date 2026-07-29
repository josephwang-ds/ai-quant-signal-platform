import { permanentRedirect } from "next/navigation";

/** Legacy v0 dashboard — permanently retired in favor of Research Home. */
export default function LegacyDashboardPage() {
  permanentRedirect("/platform");
}
