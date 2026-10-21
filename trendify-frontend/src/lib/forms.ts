import { ApiError } from "@/lib/api";

/** The server's message for one form field, if it reported one. */
export const fieldError = (error: unknown, name: string) =>
  error instanceof ApiError ? error.field(name) : undefined;

/** Password rules shown to the user; the server enforces the same policy. */
export const PASSWORD_HINT =
  "At least 10 characters, with upper- and lower-case letters and a number.";
