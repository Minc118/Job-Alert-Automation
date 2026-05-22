import type { AuthMode } from "./types";

const requestedAuthMode = import.meta.env.VITE_AUTH_MODE ?? "mock";
const neonAuthUrl = import.meta.env.VITE_NEON_AUTH_URL?.trim() ?? "";

export const authConfig: {
  mode: AuthMode;
  neonAuthUrl: string | null;
  notice: string | null;
} =
  requestedAuthMode === "neon" && neonAuthUrl
    ? {
        mode: "neon",
        neonAuthUrl,
        notice: null,
      }
    : {
        mode: "mock",
        neonAuthUrl: null,
        notice:
          requestedAuthMode === "neon"
            ? "Neon Auth mode requested without VITE_NEON_AUTH_URL. Using mock auth for this frontend session."
            : null,
      };
