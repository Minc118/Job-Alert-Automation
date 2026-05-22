import { createAuthClient, createInternalNeonAuth } from "@neondatabase/neon-js/auth";
import { BetterAuthReactAdapter } from "@neondatabase/neon-js/auth/react/adapters";
import { authConfig } from "./authConfig";

export const neonAuth =
  authConfig.mode === "neon" && authConfig.neonAuthUrl
    ? createInternalNeonAuth(authConfig.neonAuthUrl, {
        adapter: BetterAuthReactAdapter(),
      })
    : null;

export const neonAuthClient =
  authConfig.mode === "neon" && authConfig.neonAuthUrl
    ? createAuthClient(authConfig.neonAuthUrl, {
        adapter: BetterAuthReactAdapter(),
      })
    : null;
