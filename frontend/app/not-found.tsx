import Link from "next/link";

// 未知路由时显示，并提供返回首页链接
export default function NotFound() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      <h1 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>Page not found</h1>
      <p style={{ color: "#a0a0b0", marginBottom: "1.25rem", maxWidth: "24rem" }}>
        This app only has one page. Open the dashboard at the root URL.
      </p>
      <Link
        href="/"
        style={{
          padding: "0.625rem 1.25rem",
          fontSize: "0.9375rem",
          color: "#e8e8ed",
          backgroundColor: "#1e1e2e",
          border: "1px solid #2e2e3e",
          borderRadius: "0.375rem",
          textDecoration: "none",
        }}
      >
        Go to Dashboard
      </Link>
    </main>
  );
}
