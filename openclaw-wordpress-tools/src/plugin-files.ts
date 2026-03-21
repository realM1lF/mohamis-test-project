import { mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import { existsSync, realpathSync } from "node:fs";
import { normalize, relative, resolve, sep } from "node:path";
import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk/core";

const MAX_READ_BYTES = 2 * 1024 * 1024;
const MAX_WRITE_BYTES = 512 * 1024;
const MAX_PATH_LEN = 2048;
const SLUG_PATTERN = /^[a-z0-9][a-z0-9-]{0,63}$/;

function readWordpressPath(api: OpenClawPluginApi): string {
  const raw = api.pluginConfig;
  if (raw && typeof raw === "object") {
    const c = raw as Record<string, unknown>;
    const p = c.wordpressPath;
    if (typeof p === "string" && p.trim()) {
      return p.trim();
    }
  }
  return (process.env.WORDPRESS_PATH ?? "").trim();
}

function assertNoDotDot(rel: string): void {
  const n = normalize(rel.replace(/\\/g, "/"));
  if (!n || n === ".") {
    return;
  }
  const parts = n.split(/[/\\]/);
  if (parts.some((p) => p === "..")) {
    throw new Error("relativePath must not contain '..'");
  }
}

function resolvePluginRoot(wordpressRootResolved: string, slug: string): string {
  return resolve(wordpressRootResolved, "wp-content", "plugins", slug);
}

function resolveTargetPath(pluginRootResolved: string, relativePath: string): string {
  const rel = relativePath.trim() === "" ? "." : relativePath.trim();
  assertNoDotDot(rel);
  const joined = resolve(pluginRootResolved, rel);
  const relCheck = relative(pluginRootResolved, joined);
  if (relCheck.startsWith("..") || relCheck.split(sep).includes("..")) {
    throw new Error("path escapes plugin directory");
  }
  return joined;
}

const WordPressPluginFilesSchema = Type.Object(
  {
    operation: Type.Union([Type.Literal("list"), Type.Literal("read"), Type.Literal("write")], {
      description: "list: directory entries under relativePath; read: file contents; write: create or overwrite file.",
    }),
    pluginSlug: Type.String({
      description: 'Plugin directory name under wp-content/plugins/ (lowercase, hyphens), e.g. "my-addon".',
      minLength: 1,
      maxLength: 64,
      pattern: "^[a-z0-9][a-z0-9-]{0,63}$",
    }),
    relativePath: Type.String({
      description:
        'Path relative to the plugin directory. Use "" or "." for plugin root (list only). No ".." segments.',
      maxLength: MAX_PATH_LEN,
    }),
    content: Type.Optional(
      Type.String({
        description: "File body for operation write (UTF-8).",
        maxLength: MAX_WRITE_BYTES,
      }),
    ),
    overwrite: Type.Optional(
      Type.Boolean({
        description: "For write: if true, replace existing file; if false (default), fail if file exists.",
        default: false,
      }),
    ),
  },
  { additionalProperties: false },
);

type WordPressPluginFilesParams = Static<typeof WordPressPluginFilesSchema>;

export function createWordPressPluginFilesTool(api: OpenClawPluginApi): AnyAgentTool {
  return {
    name: "wordpress_plugin_files",
    label: "WordPress plugin files",
    description:
      "List, read, or write files only under wp-content/plugins/<pluginSlug>/ relative to WORDPRESS_PATH (or config wordpressPath). No path traversal; write size capped. Requires filesystem access to the WordPress installation from the gateway host.",
    parameters: WordPressPluginFilesSchema,
    execute: async (_toolCallId, rawParams) => {
      const params = rawParams as WordPressPluginFilesParams;
      const wpPathRaw = readWordpressPath(api);
      if (!wpPathRaw) {
        return {
          content: [
            {
              type: "text",
              text: "wordpress_plugin_files: missing WORDPRESS_PATH or plugins.entries.wordpress-site-tools.config.wordpressPath",
            },
          ],
          details: { ok: false as const },
        };
      }

      if (!SLUG_PATTERN.test(params.pluginSlug)) {
        return {
          content: [{ type: "text", text: "wordpress_plugin_files: invalid pluginSlug" }],
          details: { ok: false as const },
        };
      }

      if (params.relativePath.length > MAX_PATH_LEN) {
        return {
          content: [{ type: "text", text: "wordpress_plugin_files: relativePath too long" }],
          details: { ok: false as const },
        };
      }

      let wordpressRoot: string;
      try {
        wordpressRoot = realpathSync(wpPathRaw);
      } catch {
        return {
          content: [
            {
              type: "text",
              text: `wordpress_plugin_files: WORDPRESS_PATH does not exist or is not readable: ${wpPathRaw}`,
            },
          ],
          details: { ok: false as const },
        };
      }

      const pluginsDir = resolve(wordpressRoot, "wp-content", "plugins");
      if (!existsSync(pluginsDir)) {
        return {
          content: [
            {
              type: "text",
              text: `wordpress_plugin_files: wp-content/plugins not found under ${wordpressRoot}`,
            },
          ],
          details: { ok: false as const },
        };
      }

      let pluginRoot: string;
      try {
        pluginRoot = resolvePluginRoot(wordpressRoot, params.pluginSlug);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_plugin_files: ${msg}` }],
          details: { ok: false as const },
        };
      }

      let targetPath: string;
      try {
        targetPath = resolveTargetPath(pluginRoot, params.relativePath);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_plugin_files: ${msg}` }],
          details: { ok: false as const },
        };
      }

      try {
        if (params.operation === "list") {
          const dir = targetPath;
          if (!existsSync(dir)) {
            return {
              content: [
                {
                  type: "text",
                  text: `wordpress_plugin_files: directory does not exist: ${dir}`,
                },
              ],
              details: { ok: false as const },
            };
          }
          const st = await stat(dir);
          if (!st.isDirectory()) {
            return {
              content: [{ type: "text", text: "wordpress_plugin_files: list target is not a directory" }],
              details: { ok: false as const },
            };
          }
          const names = await readdir(dir);
          return {
            content: [
              {
                type: "text",
                text: `wordpress_plugin_files list ok (${names.length} entries):\n${names.join("\n")}`,
              },
            ],
            details: { ok: true as const, count: names.length },
          };
        }

        if (params.operation === "read") {
          const filePath = targetPath;
          if (!existsSync(filePath)) {
            return {
              content: [{ type: "text", text: `wordpress_plugin_files: file not found: ${filePath}` }],
              details: { ok: false as const },
            };
          }
          const st = await stat(filePath);
          if (!st.isFile()) {
            return {
              content: [{ type: "text", text: "wordpress_plugin_files: read target is not a file" }],
              details: { ok: false as const },
            };
          }
          if (st.size > MAX_READ_BYTES) {
            return {
              content: [
                {
                  type: "text",
                  text: `wordpress_plugin_files: file too large (${st.size} bytes, max ${MAX_READ_BYTES})`,
                },
              ],
              details: { ok: false as const },
            };
          }
          const buf = await readFile(filePath);
          const text = buf.toString("utf8");
          return {
            content: [
              {
                type: "text",
                text: `wordpress_plugin_files read ok (${text.length} chars):\n\n${text}`,
              },
            ],
            details: { ok: true as const, bytes: buf.length },
          };
        }

        // write
        if (params.content === undefined) {
          return {
            content: [{ type: "text", text: "wordpress_plugin_files: write requires content" }],
            details: { ok: false as const },
          };
        }
        const body = params.content;
        const bodyBytes = Buffer.byteLength(body, "utf8");
        if (bodyBytes > MAX_WRITE_BYTES) {
          return {
            content: [
              {
                type: "text",
                text: `wordpress_plugin_files: content too large (${bodyBytes} bytes, max ${MAX_WRITE_BYTES})`,
              },
            ],
            details: { ok: false as const },
          };
        }

        const filePath = targetPath;
        const overwrite = params.overwrite === true;
        if (existsSync(filePath)) {
          const st = await stat(filePath);
          if (!st.isFile()) {
            return {
              content: [{ type: "text", text: "wordpress_plugin_files: write path exists and is not a file" }],
              details: { ok: false as const },
            };
          }
          if (!overwrite) {
            return {
              content: [
                {
                  type: "text",
                  text: "wordpress_plugin_files: file exists; set overwrite true to replace",
                },
              ],
              details: { ok: false as const },
            };
          }
        } else {
          const parent = resolve(filePath, "..");
          if (!parent.startsWith(pluginRoot) && parent !== pluginRoot) {
            return {
              content: [{ type: "text", text: "wordpress_plugin_files: invalid parent path" }],
              details: { ok: false as const },
            };
          }
          await mkdir(parent, { recursive: true });
        }

        await writeFile(filePath, body, "utf8");
        return {
          content: [
            {
              type: "text",
              text: `wordpress_plugin_files write ok: ${filePath} (${bodyBytes} bytes)`,
            },
          ],
          details: { ok: true as const, path: filePath, bytes: bodyBytes },
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_plugin_files: ${msg}` }],
          details: { ok: false as const },
        };
      }
    },
  };
}
