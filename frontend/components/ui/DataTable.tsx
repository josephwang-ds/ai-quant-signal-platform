import type { ReactNode } from "react";

type DataTableProps = {
  children: ReactNode;
  className?: string;
};

export default function DataTable({ children, className }: DataTableProps) {
  const classes = ["table-scroll", className].filter(Boolean).join(" ");
  return (
    <div className={classes}>
      <table className="data-table">{children}</table>
    </div>
  );
}
