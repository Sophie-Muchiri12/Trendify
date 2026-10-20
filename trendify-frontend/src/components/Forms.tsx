import { Link, Navigate, useLocation } from "@tanstack/react-router";
import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { statusLabel, type OrderStatus } from "@/lib/orders";

const inputClass =
  "w-full rounded-2xl border bg-card px-4 py-3 text-sm outline-none focus:border-terracotta aria-[invalid=true]:border-destructive";

type FieldProps = { label: string; error?: string | undefined; hint?: string | undefined };

export function Field({
  label,
  error,
  hint,
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const id = props.id ?? props.name;
  return (
    <label className="block space-y-1.5" htmlFor={id}>
      <span className="text-sm font-semibold">{label}</span>
      <input id={id} aria-invalid={Boolean(error)} className={inputClass} {...props} />
      {error ? (
        <span className="block text-xs text-destructive">{error}</span>
      ) : hint ? (
        <span className="block text-xs text-muted-foreground">{hint}</span>
      ) : null}
    </label>
  );
}

export function TextArea({
  label,
  error,
  ...props
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = props.id ?? props.name;
  return (
    <label className="block space-y-1.5" htmlFor={id}>
      <span className="text-sm font-semibold">{label}</span>
      <textarea id={id} aria-invalid={Boolean(error)} className={inputClass} {...props} />
      {error && <span className="block text-xs text-destructive">{error}</span>}
    </label>
  );
}

export function Button({
  children,
  busy,
  variant = "primary",
  className = "",
  ...props
}: {
  children: ReactNode;
  busy?: boolean;
  variant?: "primary" | "accent" | "outline" | "danger";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const styles = {
    primary: "bg-primary text-primary-foreground",
    accent: "bg-terracotta text-terracotta-foreground",
    outline: "border bg-card",
    danger: "border border-destructive text-destructive bg-card",
  }[variant];
  return (
    <button
      disabled={busy || props.disabled}
      className={`rounded-full px-6 py-3 text-sm font-semibold transition disabled:opacity-50 ${styles} ${className}`}
      {...props}
    >
      {busy ? "Please wait…" : children}
    </button>
  );
}

/** Top-of-form error banner. Field-specific messages are shown next to each field. */
export function FormError({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <p role="alert" className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {message}
    </p>
  );
}

export const fieldError = (error: unknown, name: string) =>
  error instanceof ApiError ? error.field(name) : undefined;

export function Page({
  title,
  children,
  narrow,
}: {
  title: string;
  children: ReactNode;
  narrow?: boolean;
}) {
  return (
    <div className={`mx-auto px-5 pt-10 ${narrow ? "max-w-md" : "max-w-5xl"}`}>
      <h1 className="mb-8 text-4xl md:text-5xl">{title}</h1>
      {children}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-3xl border bg-card p-6 ${className}`}>{children}</section>;
}

/**
 * Show the page only to signed-in users (optionally admins). This is a convenience for
 * the UI; the server enforces the same rules on every request.
 */
export function RequireAuth({ children, admin }: { children: ReactNode; admin?: boolean }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <p className="py-32 text-center text-muted-foreground">Loading…</p>;
  if (!user) return <Navigate to="/login" search={{ redirect: location.href }} replace />;
  if (admin && user.role !== "admin")
    return (
      <div className="py-32 text-center">
        <h1 className="text-4xl">Not allowed</h1>
        <p className="mt-3 text-muted-foreground">This area is for administrators.</p>
        <Link to="/" className="mt-6 inline-block underline">
          Go home
        </Link>
      </div>
    );
  return <>{children}</>;
}

const statusColours: Record<OrderStatus, string> = {
  pending_payment: "bg-ochre/20 text-foreground",
  paid: "bg-indigo/15 text-indigo",
  shipped: "bg-plum/15 text-plum",
  delivered: "bg-green-600/15 text-green-800",
  cancelled: "bg-muted text-muted-foreground",
  refunded: "bg-muted text-muted-foreground",
};

export function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColours[status]}`}>
      {statusLabel[status]}
    </span>
  );
}

/** Password rules shown to the user; the server enforces the same policy. */
export const PASSWORD_HINT =
  "At least 10 characters, with upper- and lower-case letters and a number.";
