import { existsSync, statSync } from "node:fs";
import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import { tryResolveAuthPair, tryResolveBaseUrl } from "./credentials.js";
import {
  getWpCliRunnerConfigError,
  resolveWpCliRunner,
  runWpCli,
} from "./wp-cli.js";

const CHECK_TIMEOUT_MS = 30_000;

const WordPressConnectionCheckSchema = Type.Object(
  {
    includeWpCli: Type.Optional(
      Type.Boolean({
        description:
          "Run WP-CLI `core version` when WORDPRESS_PATH (or plugin wordpressPath) is set. Default: true if a WordPress path is configured, otherwise false.",
      }),
    ),
  },
  { additionalProperties: false },
);

type WordPressConnectionCheckParams = Static<typeof WordPressConnectionCheckSchema>;

function wpJsonRootUrl(baseUrl: string): string {
  const base = `${baseUrl.replace(/\/+$/, "")}/`;
  return new URL("wp-json/", base).toString();
}

function usersMeUrl(baseUrl: string): string {
  const base = `${baseUrl.replace(/\/+$/, "")}/`;
  return new URL("wp-json/wp/v2/users/me", base).toString();
}

function readWordpressPath(api: OpenClawPluginApi): string {
  const raw = api.pluginConfig;
  if (!raw || typeof raw !== "object") {
    return (process.env.WORDPRESS_PATH ?? "").trim();
  }
  const c = raw as Record<string, unknown>;
  const fromCfg = typeof c.wordpressPath === "string" ? c.wordpressPath : undefined;
  return (fromCfg ?? process.env.WORDPRESS_PATH ?? "").trim();
}

export function createWordPressConnectionCheckTool(api: OpenClawPluginApi): AnyAgentTool {
  return {
    name: "wordpress_connection_check",
    label: "WordPress connection check",
    description:
      "Verify reachability of the WordPress REST API (anonymous wp-json), optional Application Password auth (wp/v2/users/me), and optionally WP-CLI core version (wp or ddev wp per wpCliRunner / WORDPRESS_WP_CLI_RUNNER). Use after configuring WORDPRESS_* env or plugin config; no secrets in output.",
    parameters: WordPressConnectionCheckSchema,
    execute: async (_toolCallId, rawParams) => {
      const params = rawParams as WordPressConnectionCheckParams;
      const lines: string[] = ["=== wordpress_connection_check ===", ""];

      const baseRes = tryResolveBaseUrl(api);
      if ("missing" in baseRes) {
        lines.push("REST base URL: missing (set WORDPRESS_SITE_URL or config baseUrl)");
        lines.push("REST discovery (wp-json): skipped");
        lines.push("REST auth (users/me): skipped");
      } else {
        const { baseUrl } = baseRes;
        lines.push(`REST base URL: ${baseUrl}`);

        const root = wpJsonRootUrl(baseUrl);
        try {
          const res = await fetch(root, {
            method: "GET",
            headers: { Accept: "application/json" },
            redirect: "manual",
          });
          lines.push(`REST discovery: GET wp-json/ -> HTTP ${res.status} ${res.statusText}`);
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          lines.push(`REST discovery: fetch failed: ${msg}`);
        }

        const auth = tryResolveAuthPair(api);
        if ("missing" in auth) {
          lines.push("REST auth: skipped (set WORDPRESS_USER + WORDPRESS_APPLICATION_PASSWORD or config)");
        } else {
          const meUrl = usersMeUrl(baseUrl);
          const headers: Record<string, string> = {
            Accept: "application/json",
            Authorization:
              "Basic " +
              Buffer.from(`${auth.user}:${auth.applicationPassword}`, "utf8").toString("base64"),
          };
          try {
            const res = await fetch(meUrl, { method: "GET", headers, redirect: "manual" });
            lines.push(`REST auth: GET wp/v2/users/me -> HTTP ${res.status} ${res.statusText}`);
          } catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            lines.push(`REST auth: fetch failed: ${msg}`);
          }
        }
      }

      const cwd = readWordpressPath(api);
      const defaultIncludeWpCli = Boolean(cwd);
      const includeWpCli = params.includeWpCli ?? defaultIncludeWpCli;

      lines.push("");
      if (!includeWpCli) {
        lines.push("WP-CLI: skipped (includeWpCli=false)");
      } else if (!cwd) {
        lines.push("WP-CLI: skipped (no WORDPRESS_PATH or config wordpressPath)");
      } else if (!existsSync(cwd) || !statSync(cwd).isDirectory()) {
        lines.push(`WP-CLI: skipped (not a directory: ${cwd})`);
      } else {
        const runnerErr = getWpCliRunnerConfigError(api);
        if (runnerErr) {
          lines.push(`WP-CLI: skipped (${runnerErr})`);
        } else {
          const runner = resolveWpCliRunner(api);
          const result = await runWpCli(cwd, ["core", "version"], CHECK_TIMEOUT_MS, runner);
          if (result.timedOut) {
            lines.push(`WP-CLI: timed out after ${CHECK_TIMEOUT_MS}ms (cwd: ${cwd}, runner: ${runner})`);
          } else {
            const ver = (result.stdout + result.stderr).trim() || "(no output)";
            const cmd = runner === "ddev" ? "ddev wp core version" : "wp core version";
            lines.push(`WP-CLI: cwd ${cwd}`);
            lines.push(`WP-CLI: runner ${runner}`);
            lines.push(`WP-CLI: ${cmd} -> exit ${result.code ?? "null"}`);
            lines.push(`WP-CLI: output: ${ver.slice(0, 500)}${ver.length > 500 ? "…" : ""}`);
          }
        }
      }

      return {
        content: [{ type: "text", text: lines.join("\n") }],
        details: { ok: true as const },
      };
    },
  };
}
