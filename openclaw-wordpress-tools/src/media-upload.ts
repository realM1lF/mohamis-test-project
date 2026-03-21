import { realpathSync, statSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { basename, resolve, sep } from "node:path";
import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import { resolveCredentials } from "./credentials.js";

const MAX_FILE_BYTES = 25 * 1024 * 1024;
const MAX_RESPONSE_PREVIEW_CHARS = 512 * 1024;

const WordPressMediaUploadSchema = Type.Object(
  {
    sourcePath: Type.String({
      minLength: 1,
      maxLength: 4096,
      description:
        "Path to a local file to upload. Resolved with path.resolve(process.cwd(), …); must lie under process.cwd() (after realpath). Max size 25 MiB.",
    }),
  },
  { additionalProperties: false },
);

type WordPressMediaUploadParams = Static<typeof WordPressMediaUploadSchema>;

function buildMediaUrl(baseUrl: string): string {
  const base = `${baseUrl.replace(/\/+$/, "")}/`;
  return new URL("wp-json/wp/v2/media", base).toString();
}

function assertFileUnderCwd(sourcePath: string): { absolutePath: string; byteLength: number } {
  const resolved = resolve(process.cwd(), sourcePath);
  let st;
  try {
    st = statSync(resolved);
  } catch {
    throw new Error(`sourcePath not found or not accessible: ${sourcePath}`);
  }
  if (!st.isFile()) {
    throw new Error(`sourcePath is not a regular file: ${resolved}`);
  }
  if (st.size > MAX_FILE_BYTES) {
    throw new Error(`file exceeds max size (${MAX_FILE_BYTES} bytes): ${resolved}`);
  }
  const realFile = realpathSync(resolved);
  let realCwd: string;
  try {
    realCwd = realpathSync(process.cwd());
  } catch {
    throw new Error("process.cwd() could not be resolved");
  }
  if (realFile !== realCwd && !realFile.startsWith(realCwd + sep)) {
    throw new Error(
      `resolved file must be under process.cwd() (${realCwd}); got ${realFile}`,
    );
  }
  return { absolutePath: realFile, byteLength: st.size };
}

function truncate(text: string, max: number): string {
  if (text.length <= max) {
    return text;
  }
  return text.slice(0, max) + "\n\n… [truncated]";
}

export function createWordPressMediaUploadTool(api: OpenClawPluginApi): AnyAgentTool {
  return {
    name: "wordpress_media_upload",
    label: "WordPress media upload",
    description:
      "Upload a local file to the WordPress media library via REST multipart POST (wp/v2/media). File must be under the gateway process cwd (max 25 MiB). Uses same credentials as wordpress_rest_request.",
    parameters: WordPressMediaUploadSchema,
    execute: async (_toolCallId, rawParams) => {
      const params = rawParams as WordPressMediaUploadParams;
      let creds: ReturnType<typeof resolveCredentials>;
      try {
        creds = resolveCredentials(api);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_media_upload: ${msg}` }],
          details: { ok: false as const },
        };
      }

      let fileInfo: { absolutePath: string; byteLength: number };
      try {
        fileInfo = assertFileUnderCwd(params.sourcePath);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_media_upload: ${msg}` }],
          details: { ok: false as const },
        };
      }

      const buf = await readFile(fileInfo.absolutePath);
      const name = basename(fileInfo.absolutePath);
      const blob = new Blob([buf]);
      const form = new FormData();
      form.set("file", blob, name);

      const url = buildMediaUrl(creds.baseUrl);
      const headers: Record<string, string> = {
        Authorization:
          "Basic " +
          Buffer.from(`${creds.user}:${creds.applicationPassword}`, "utf8").toString("base64"),
      };

      let res: Response;
      try {
        res = await fetch(url, { method: "POST", headers, body: form, redirect: "manual" });
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [
            { type: "text", text: `wordpress_media_upload: fetch failed: ${msg}\nURL: ${url}` },
          ],
          details: { ok: false as const, url },
        };
      }

      const bodyText = await res.text();
      const preview = truncate(bodyText, MAX_RESPONSE_PREVIEW_CHARS);

      const lines = [
        `HTTP ${res.status} ${res.statusText}`,
        `URL: ${url}`,
        `file: ${fileInfo.absolutePath} (${fileInfo.byteLength} bytes)`,
        "",
        preview,
      ];

      return {
        content: [{ type: "text", text: lines.join("\n") }],
        details: {
          ok: true as const,
          status: res.status,
          url,
          bytes: bodyText.length,
        },
      };
    },
  };
}
