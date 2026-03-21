import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk/core";
import { createWordPressConnectionCheckTool } from "./src/connection-check.js";
import { resolveCredentials } from "./src/credentials.js";
import { createWordPressMediaUploadTool } from "./src/media-upload.js";
import { createWordPressWpCliTool } from "./src/wp-cli.js";
import { createWordPressPluginFilesTool } from "./src/plugin-files.js";

const MAX_BODY_CHARS = 2 * 1024 * 1024;
const MAX_RESPONSE_PREVIEW_CHARS = 512 * 1024;

const HttpMethodSchema = Type.Union(
  [
    Type.Literal("GET"),
    Type.Literal("POST"),
    Type.Literal("PUT"),
    Type.Literal("PATCH"),
    Type.Literal("DELETE"),
  ],
  { description: "HTTP method for the WordPress REST request." },
);

const WordPressRestRequestSchema = Type.Object(
  {
    method: HttpMethodSchema,
    path: Type.String({
      description:
        'REST path under /wp-json (e.g. "wp/v2/posts" or "wc/v3/products"). No leading slash required; must not contain ".." or a full URL.',
      minLength: 1,
      maxLength: 2048,
    }),
    query: Type.Optional(
      Type.Record(Type.String(), Type.String(), {
        description: "Optional query parameters (all values as strings).",
      }),
    ),
    body: Type.Optional(
      Type.String({
        description: "Optional JSON body for POST, PUT, or PATCH.",
        maxLength: MAX_BODY_CHARS,
      }),
    ),
  },
  { additionalProperties: false },
);

type WordPressRestRequestParams = Static<typeof WordPressRestRequestSchema>;

function normalizeRestPath(path: string): string {
  const p = path.trim().replace(/^\/+/, "");
  if (!p) {
    throw new Error("path must not be empty");
  }
  if (p.includes("..")) {
    throw new Error('path must not contain ".."');
  }
  if (/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(p)) {
    throw new Error("path must be a wp-json sub-path, not an absolute URL");
  }
  return p;
}

function buildUrl(baseUrl: string, restPath: string, query?: Record<string, string>): string {
  const pathPart = encodeURI(restPath.replace(/\\/g, "/"));
  // Relative to base (supports WP in subdirectory); avoid leading "/" on first arg.
  const base = `${baseUrl.replace(/\/+$/, "")}/`;
  const url = new URL(`wp-json/${pathPart}`, base);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      url.searchParams.set(k, v);
    }
  }
  return url.toString();
}

function truncate(text: string, max: number): { text: string; truncated: boolean } {
  if (text.length <= max) {
    return { text, truncated: false };
  }
  return { text: text.slice(0, max) + "\n\n… [truncated]", truncated: true };
}

function createWordPressRestTool(api: OpenClawPluginApi): AnyAgentTool {
  return {
    name: "wordpress_rest_request",
    label: "WordPress REST",
    description:
      "Call the WordPress REST API on the configured site (WORDPRESS_SITE_URL + Application Password). Use a path under wp-json only, e.g. wp/v2/posts or wc/v3/products. Prefer this over ad-hoc curl when available.",
    parameters: WordPressRestRequestSchema,
    execute: async (_toolCallId, rawParams) => {
      const params = rawParams as WordPressRestRequestParams;
      let creds: ReturnType<typeof resolveCredentials>;
      try {
        creds = resolveCredentials(api);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_rest_request: ${msg}` }],
          details: { ok: false as const },
        };
      }

      let restPath: string;
      try {
        restPath = normalizeRestPath(params.path);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [{ type: "text", text: `wordpress_rest_request: invalid path: ${msg}` }],
          details: { ok: false as const },
        };
      }

      const url = buildUrl(creds.baseUrl, restPath, params.query);
      const headers: Record<string, string> = {
        Accept: "application/json",
        Authorization:
          "Basic " +
          Buffer.from(`${creds.user}:${creds.applicationPassword}`, "utf8").toString("base64"),
      };

      const init: RequestInit = {
        method: params.method,
        headers,
        redirect: "manual",
      };

      if (params.body !== undefined && ["POST", "PUT", "PATCH"].includes(params.method)) {
        headers["Content-Type"] = "application/json";
        init.body = params.body;
      }

      let res: Response;
      try {
        res = await fetch(url, init);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
          content: [
            {
              type: "text",
              text: `wordpress_rest_request: fetch failed: ${msg}\nURL: ${url}`,
            },
          ],
          details: { ok: false as const, url },
        };
      }

      const bodyText = await res.text();
      const { text: preview, truncated } = truncate(bodyText, MAX_RESPONSE_PREVIEW_CHARS);

      const lines = [
        `HTTP ${res.status} ${res.statusText}`,
        `URL: ${url}`,
        truncated ? `Response body truncated to ${MAX_RESPONSE_PREVIEW_CHARS} chars.` : "",
        "",
        preview,
      ].filter(Boolean);

      return {
        content: [{ type: "text", text: lines.join("\n") }],
        details: {
          ok: true as const,
          status: res.status,
          url,
          truncated,
          bytes: bodyText.length,
        },
      };
    },
  };
}

export default function register(api: OpenClawPluginApi) {
  api.registerTool(createWordPressRestTool(api), { optional: true });
  api.registerTool(createWordPressWpCliTool(api), { optional: true });
  api.registerTool(createWordPressConnectionCheckTool(api), { optional: true });
  api.registerTool(createWordPressMediaUploadTool(api), { optional: true });
  api.registerTool(createWordPressPluginFilesTool(api), { optional: true });
}
