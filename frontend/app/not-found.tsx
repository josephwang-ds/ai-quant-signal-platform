import Link from "next/link";

// 未知路由时显示，并提供返回首页链接
export default function NotFound() {
  return (
    <main className="route-state-page">
      <div className="route-state-card">
      <p className="route-state-card__eyebrow">404</p>
      <h1>Page not found</h1>
      <p>
        This route is not part of the current research workspace. Return to the research library to continue.
      </p>
      <Link
        href="/"
        className="btn btn--primary"
      >
        Open Research Library
      </Link>
      </div>
    </main>
  );
}
