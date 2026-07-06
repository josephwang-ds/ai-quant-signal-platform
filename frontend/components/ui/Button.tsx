import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  primary?: boolean;
};

export default function Button({ children, primary = false, className = "", ...props }: ButtonProps) {
  const classes = ["btn", primary ? "btn--primary" : "", className].filter(Boolean).join(" ");
  return (
    <button type="button" className={classes} {...props}>
      {children}
    </button>
  );
}
