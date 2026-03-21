import { spawn } from "node:child_process";
import { existsSync, statSync } from "node:fs";
import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import {
  BUILTIN_DEFAULT_PREFIXES,
  getAllowPrefixesForProfile,
  isWpCliProfileName,
  WP_CLI_PROFILE_NAMES,
} from "./wp-cli-presets.js";

const MAX_ARGS = 64;
const MAX_ARG_LENGTH = 512;
const TIMEOUT_MS = 120_000;
const MAX_COMBINED_OUTPUT_CHARS = 512 * 1024;

/** Safe argv fragment: no shell metacharacters, one CLI token per element. */
const SAFE_ARG_PATTERN = /^[\w.=@:\/%*+,[\]{}\\-]+$/;

const WordPressWpCliSchema = Type.Object(
  {
    args: Type.Array(
      Type.String({
        minLength: 1,
        maxLength: MAX_ARG_LENGTH,
        description:
          "Arguments after `wp` (e.g. [\"core\", \"version\"] or [\"post\", \"list\", \"--post_type=page\"]). Must match allowlisted prefix and global blocklist.",
      }),
      {
        minItems: 1,
        maxItems: MAX_ARGS,
        description: "WP-CLI arguments only; do not include the `wp` binary name.",
      },
    ),
  },
  { additionalProperties: false },
);

type WordPressWpCliParams = Static<typeof WordPressWpCliSchema>;

export type WpCliRunner = "wp" | "ddev";

function readWpCliConfig(api: OpenClawPluginApi): {
  wordpressPath?: string;
  wpCliAllowPrefixes?: string[];
  wpCliProfile?: string;
  wpCliRunner?: string;
} {
  const raw = api.pluginConfig;
  if (!raw || typeof raw !== "object") {
    return {};
  }
  const c = raw as Record<string, unknown>;
  const wordpressPath = typeof c.wordpressPath === "string" ? c.wordpressPath : undefined;
  let wpCliAllowPrefixes: string[] | undefined;
  if (Array.isArray(c.wpCliAllowPrefixes)) {
    wpCliAllowPrefixes = c.wpCliAllowPrefixes.filter((x): x is string => typeof x === "string");
  }
  const wpCliProfile = typeof c.wpCliProfile === "string" ? c.wpCliProfile : undefined;
  const wpCliRunner = typeof c.wpCliRunner === "string" ? c.wpCliRunner : undefined;
  return { wordpressPath, wpCliAllowPrefixes, wpCliProfile, wpCliRunner };
}

function isValidWpCliRunnerToken(s: string): s is WpCliRunner {
  const t = s.trim().toLowerCase();
  return t === "wp" || t === "ddev";
}

/** Env WORDPRESS_WP_CLI_RUNNER overrides plugin config when set to wp or ddev. */
export function resolveWpCliRunner(api: OpenClawPluginApi): WpCliRunner {
  const env = process.env.WORDPRESS_WP_CLI_RUNNER?.trim().toLowerCase();
  if (env === "wp" || env === "ddev") {
    return env;
  }
  const cfg = readWpCliConfig(api).wpCliRunner?.trim().toLowerCase();
  if (cfg === "ddev" || cfg === "wp") {
    return cfg;
  }
  return "wp";
}

export function getWpCliRunnerConfigError(api: OpenClawPluginApi): string | null {
  const envRaw = process.env.WORDPRESS_WP_CLI_RUNNER?.trim();
  if (envRaw && !isValidWpCliRunnerToken(envRaw)) {
    return `invalid WORDPRESS_WP_CLI_RUNNER "${envRaw}" (use wp or ddev)`;
  }
  const cfgRaw = readWpCliConfig(api).wpCliRunner?.trim();
  if (cfgRaw && !isValidWpCliRunnerToken(cfgRaw)) {
    return `invalid wpCliRunner in plugin config "${cfgRaw}" (use wp or ddev)`;
  }
  return null;
}

function resolveWordPressPath(api: OpenClawPluginApi): string {
  const cfg = readWpCliConfig(api);
  return (cfg.wordpressPath ?? process.env.WORDPRESS_PATH ?? "").trim();
}

function parseAllowPrefixesFromConfig(strings: string[]): string[][] {
  return strings.map((s) =>
    s
      .trim()
      .split(/\s+/)
      .filter((t) => t.length > 0),
  );
}

function getWpCliProfileConfigError(api: OpenClawPluginApi): string | null {
  const { wpCliAllowPrefixes, wpCliProfile } = readWpCliConfig(api);
  const hasManual = wpCliAllowPrefixes && wpCliAllowPrefixes.length > 0;
  if (hasManual) {
    return null;
  }
  const p = wpCliProfile?.trim();
  if (!p) {
    return null;
  }
  if (!isWpCliProfileName(p)) {
    return `unknown wpCliProfile "${p}" (expected one of: ${WP_CLI_PROFILE_NAMES.join(", ")})`;
  }
  return null;
}

function getEffectiveAllowPrefixes(api: OpenClawPluginApi): string[][] {
  const { wpCliAllowPrefixes, wpCliProfile } = readWpCliConfig(api);
  if (wpCliAllowPrefixes && wpCliAllowPrefixes.length > 0) {
    const parsed = parseAllowPrefixesFromConfig(wpCliAllowPrefixes);
    return parsed.filter((p) => p.length > 0);
  }
  const profile = wpCliProfile?.trim();
  if (profile) {
    const fromPreset = getAllowPrefixesForProfile(profile);
    if (fromPreset) {
      return fromPreset;
    }
  }
  return BUILTIN_DEFAULT_PREFIXES;
}

function tokensMatchPrefix(args: string[], prefix: string[]): boolean {
  if (args.length < prefix.length) {
    return false;
  }
  for (let i = 0; i < prefix.length; i++) {
    if (args[i]!.toLowerCase() !== prefix[i]!.toLowerCase()) {
      return false;
    }
  }
  return true;
}

function isAllowedByPrefixList(args: string[], prefixes: string[][]): boolean {
  return prefixes.some((p) => tokensMatchPrefix(args, p));
}

/**
 * Always denied regardless of allowlist (high-risk WP-CLI entry points).
 */
function isGloballyBlocked(args: string[]): string | null {
  if (args.length === 0) {
    return "empty argv";
  }
  const a0 = args[0]!.toLowerCase();
  if (a0 === "eval" || a0 === "eval-file") {
    return "blocked: eval / eval-file";
  }
  if (a0 === "shell") {
    return "blocked: shell";
  }
  if (a0 === "cli") {
    return "blocked: cli";
  }
  if (a0 === "db") {
    const a1 = args[1]?.toLowerCase();
    if (a1 === "query" || a1 === "reset" || a1 === "clean" || a1 === "import" || a1 === "export") {
      return `blocked: db ${a1}`;
    }
  }
  return null;
}

function validateArgTokens(args: string[]): string | null {
  for (const a of args) {
    if (a.length > MAX_ARG_LENGTH) {
      return `arg exceeds max length (${MAX_ARG_LENGTH})`;
    }
    if (!SAFE_ARG_PATTERN.test(a)) {
      return `arg contains disallowed characters: ${JSON.stringify(a.slice(0, 80))}`;
    }
  }
  return null;
}

function truncate(text: string, max: number): { text: string; truncated: boolean } {
  if (text.length <= max) {
    return { text, truncated: false };
  }
  return { text: text.slice(0, max) + "\n\n… [truncated]", truncated: true };
}

/**
 * Spawn WP-CLI: either `wp …` on the host or `ddev wp …` in cwd (DDEV project root).
 */
export function runWpCli(
  cwd: string,
  argv: string[],
  timeoutMs: number,
  runner: WpCliRunner,
): Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  const command = runner === "ddev" ? "ddev" : "wp";
  const spawnArgv = runner === "ddev" ? (["wp", ...argv] as string[]) : argv;

  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const finish = (payload: { code: number | null; stdout: string; stderr: string; timedOut: boolean }) => {
      if (settled) {
        return;
      }
      settled = true;
      resolve(payload);
    };

    const child = spawn(command, spawnArgv, {
      cwd,
      shell: false,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGTERM");
      setTimeout(() => child.kill("SIGKILL"), 5000).unref?.();
      finish({ code: null, stdout, stderr, timedOut: true });
    }, timeoutMs);

    const onChunk = (buf: Buffer, which: "stdout" | "stderr") => {
      const chunk = buf.toString("utf8");
      if (which === "stdout") {
        stdout += chunk;
      } else {
        stderr += chunk;
      }
      if (stdout.length + stderr.length > MAX_COMBINED_OUTPUT_CHARS * 2) {
        child.kill("SIGTERM");
      }
    };

    child.stdout?.on("data", (d: Buffer) => onChunk(d, "stdout"));
    child.stderr?.on("data", (d: Buffer) => onChunk(d, "stderr"));

    child.on("error", (err) => {
      clearTimeout(timer);
      finish({
        code: null,
        stdout,
        stderr: stderr + (err instanceof Error ? err.message : String(err)),
        timedOut: false,
      });
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      finish({ code: code ?? null, stdout, stderr, timedOut });
    });
  });
}

/** @deprecated Use runWpCli with explicit runner; kept for tests that expect plain wp. */
export function runWp(
  cwd: string,
  argv: string[],
  timeoutMs: number,
): Promise<{ code: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  return runWpCli(cwd, argv, timeoutMs, "wp");
}

export function createWordPressWpCliTool(api: OpenClawPluginApi): AnyAgentTool {
  return {
    name: "wordpress_wp_cli",
    label: "WordPress WP-CLI",
    description:
      "Run WP-CLI in WORDPRESS_PATH (or plugin config wordpressPath) with spawn (no shell). Use wpCliRunner ddev + DDEV project root cwd for DDEV (ddev wp …). Only allowlisted command prefixes (defaults, wpCliProfile preset, or wpCliAllowPrefixes override); eval/shell/cli and dangerous db subcommands are always blocked. Prefer this over raw exec when available.",
    parameters: WordPressWpCliSchema,
    execute: async (_toolCallId, rawParams) => {
      const params = rawParams as WordPressWpCliParams;
      const cwd = resolveWordPressPath(api);

      if (!cwd) {
        return {
          content: [
            {
              type: "text",
              text: "wordpress_wp_cli: missing WORDPRESS_PATH (or plugins.entries.wordpress-site-tools.config.wordpressPath)",
            },
          ],
          details: { ok: false as const },
        };
      }

      if (!existsSync(cwd) || !statSync(cwd).isDirectory()) {
        return {
          content: [{ type: "text", text: `wordpress_wp_cli: not a directory: ${cwd}` }],
          details: { ok: false as const, cwd },
        };
      }

      const args = params.args;
      const tokenErr = validateArgTokens(args);
      if (tokenErr) {
        return {
          content: [{ type: "text", text: `wordpress_wp_cli: ${tokenErr}` }],
          details: { ok: false as const },
        };
      }

      const blockReason = isGloballyBlocked(args);
      if (blockReason) {
        return {
          content: [{ type: "text", text: `wordpress_wp_cli: ${blockReason}` }],
          details: { ok: false as const },
        };
      }

      const profileErr = getWpCliProfileConfigError(api);
      if (profileErr) {
        return {
          content: [{ type: "text", text: `wordpress_wp_cli: ${profileErr}` }],
          details: { ok: false as const },
        };
      }

      const runnerErr = getWpCliRunnerConfigError(api);
      if (runnerErr) {
        return {
          content: [{ type: "text", text: `wordpress_wp_cli: ${runnerErr}` }],
          details: { ok: false as const },
        };
      }

      const runner = resolveWpCliRunner(api);

      const prefixes = getEffectiveAllowPrefixes(api);
      if (!isAllowedByPrefixList(args, prefixes)) {
        const hint =
          prefixes.length <= 8
            ? prefixes.map((p) => p.join(" ")).join("; ")
            : `${prefixes.length} configured prefix(es)`;
        return {
          content: [
            {
              type: "text",
              text:
                `wordpress_wp_cli: command not allowed by prefix list. Allowed prefixes (first tokens must match): ${hint}. ` +
                `Configure plugins.entries.wordpress-site-tools.config.wpCliAllowPrefixes (non-empty replaces all) or wpCliProfile (${WP_CLI_PROFILE_NAMES.join(", ")}).`,
            },
          ],
          details: { ok: false as const },
        };
      }

      const result = await runWpCli(cwd, args, TIMEOUT_MS, runner);
      if (result.timedOut) {
        const cmdLine =
          runner === "ddev"
            ? `ddev wp ${args.map((a) => JSON.stringify(a)).join(" ")}`
            : `wp ${args.map((a) => JSON.stringify(a)).join(" ")}`;
        return {
          content: [
            {
              type: "text",
              text: `wordpress_wp_cli: timed out after ${TIMEOUT_MS}ms\ncwd: ${cwd}\n${cmdLine}`,
            },
          ],
          details: { ok: false as const, cwd, timedOut: true },
        };
      }

      const combined = [
        result.stdout ? `--- stdout ---\n${result.stdout}` : "",
        result.stderr ? `--- stderr ---\n${result.stderr}` : "",
      ]
        .filter(Boolean)
        .join("\n");

      const { text: out, truncated } = truncate(combined || "(no output)", MAX_COMBINED_OUTPUT_CHARS);

      const invoked =
        runner === "ddev"
          ? `ddev wp ${args.map((a) => JSON.stringify(a)).join(" ")}`
          : `wp ${args.map((a) => JSON.stringify(a)).join(" ")}`;

      const header = [
        `exit: ${result.code ?? "null"}`,
        `cwd: ${cwd}`,
        `runner: ${runner}`,
        invoked,
        truncated ? `Output truncated to ${MAX_COMBINED_OUTPUT_CHARS} chars.` : "",
      ]
        .filter(Boolean)
        .join("\n");

      return {
        content: [{ type: "text", text: `${header}\n\n${out}` }],
        details: {
          ok: true as const,
          exitCode: result.code,
          cwd,
          truncated,
        },
      };
    },
  };
}
