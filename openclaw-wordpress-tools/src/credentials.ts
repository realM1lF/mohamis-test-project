import type { OpenClawPluginApi } from "openclaw/plugin-sdk/core";

export type PluginRestCfg = {
  baseUrl?: string;
  user?: string;
  applicationPassword?: string;
};

export function readPluginRestConfig(api: OpenClawPluginApi): PluginRestCfg {
  const raw = api.pluginConfig;
  if (!raw || typeof raw !== "object") {
    return {};
  }
  const c = raw as Record<string, unknown>;
  return {
    baseUrl: typeof c.baseUrl === "string" ? c.baseUrl : undefined,
    user: typeof c.user === "string" ? c.user : undefined,
    applicationPassword:
      typeof c.applicationPassword === "string" ? c.applicationPassword : undefined,
  };
}

export function resolveCredentials(api: OpenClawPluginApi): {
  baseUrl: string;
  user: string;
  applicationPassword: string;
} {
  const cfg = readPluginRestConfig(api);
  const baseUrl = (cfg.baseUrl ?? process.env.WORDPRESS_SITE_URL ?? "").trim().replace(/\/+$/, "");
  const user = (cfg.user ?? process.env.WORDPRESS_USER ?? "").trim();
  const applicationPassword = (
    cfg.applicationPassword ?? process.env.WORDPRESS_APPLICATION_PASSWORD ?? ""
  ).trim();

  if (!baseUrl) {
    throw new Error(
      "Missing WordPress base URL: set WORDPRESS_SITE_URL or plugins.entries.wordpress-site-tools.config.baseUrl",
    );
  }
  if (!user || !applicationPassword) {
    throw new Error(
      "Missing WordPress credentials: set WORDPRESS_USER and WORDPRESS_APPLICATION_PASSWORD (or plugin config user / applicationPassword)",
    );
  }

  return { baseUrl, user, applicationPassword };
}

/** Base URL only (for unauthenticated REST discovery). */
export function tryResolveBaseUrl(api: OpenClawPluginApi): { baseUrl: string } | { missing: true } {
  const cfg = readPluginRestConfig(api);
  const baseUrl = (cfg.baseUrl ?? process.env.WORDPRESS_SITE_URL ?? "").trim().replace(/\/+$/, "");
  if (!baseUrl) {
    return { missing: true };
  }
  return { baseUrl };
}

/** Application-password pair without requiring base URL. */
export function tryResolveAuthPair(
  api: OpenClawPluginApi,
): { user: string; applicationPassword: string } | { missing: true } {
  const cfg = readPluginRestConfig(api);
  const user = (cfg.user ?? process.env.WORDPRESS_USER ?? "").trim();
  const applicationPassword = (
    cfg.applicationPassword ?? process.env.WORDPRESS_APPLICATION_PASSWORD ?? ""
  ).trim();
  if (!user || !applicationPassword) {
    return { missing: true };
  }
  return { user, applicationPassword };
}
