import type { ReactNode } from "react";

type DataTableProps = {
  children: ReactNode;
};

export default function DataTable({ children }: DataTableProps) {
  return (
    <div className="table-scroll">
      <table className="data-table">{children}</table>
    </div>
  );
}
