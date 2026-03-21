/**
 * Built-in WP-CLI allowlist presets for wordpress_wp_cli.
 * Keep in sync with openclaw-wordpress-skill/references/WPCLI_PRESETS.md
 */

export const BUILTIN_DEFAULT_PREFIXES: string[][] = [
  ["core", "version"],
  ["core", "is-installed"],
  ["post", "list"],
  ["post", "get"],
  ["plugin", "list"],
  ["theme", "list"],
  ["option", "get"],
  ["user", "list"],
];

const EXTENDED_READ_PREFIXES: string[][] = [
  ["core", "version"],
  ["core", "is-installed"],
  ["core", "verify-checksums"],
  ["post", "list"],
  ["post", "get"],
  ["page", "list"],
  ["page", "get"],
  ["plugin", "list"],
  ["theme", "list"],
  ["option", "get"],
  ["user", "list"],
  ["rewrite", "list"],
  ["db", "tables"],
  ["db", "check"],
  ["db", "size"],
];

const CONTENT_STAGING_PREFIXES: string[][] = [
  ["core", "version"],
  ["post", "list"],
  ["post", "get"],
  ["post", "create"],
  ["post", "update"],
  ["post", "delete"],
  ["page", "list"],
  ["page", "get"],
  ["page", "create"],
  ["page", "update"],
  ["media", "list"],
  ["media", "get"],
  ["media", "import"],
];

const STAGING_ADMIN_PREFIXES: string[][] = [
  ["core", "version"],
  ["plugin", "list"],
  ["plugin", "status"],
  ["plugin", "activate"],
  ["plugin", "deactivate"],
  ["plugin", "install"],
  ["plugin", "update"],
  ["theme", "list"],
  ["theme", "activate"],
  ["theme", "install"],
  ["theme", "update"],
  ["cache", "flush"],
  ["rewrite", "flush"],
  ["option", "get"],
];

const DEV_LOCAL_PREFIXES: string[][] = [
  ["core", "version"],
  ["scaffold", "plugin"],
  ["scaffold", "post-type"],
  ["scaffold", "taxonomy"],
  ["i18n", "make-pot"],
  ["i18n", "make-json"],
];

export const WP_CLI_PROFILE_NAMES = [
  "builtin-default",
  "extended-read",
  "content-staging",
  "staging-admin",
  "dev-local",
] as const;

export type WpCliProfileName = (typeof WP_CLI_PROFILE_NAMES)[number];

export const WP_CLI_PRESETS: Record<WpCliProfileName, string[][]> = {
  "builtin-default": BUILTIN_DEFAULT_PREFIXES,
  "extended-read": EXTENDED_READ_PREFIXES,
  "content-staging": CONTENT_STAGING_PREFIXES,
  "staging-admin": STAGING_ADMIN_PREFIXES,
  "dev-local": DEV_LOCAL_PREFIXES,
};

export function isWpCliProfileName(s: string): s is WpCliProfileName {
  return (WP_CLI_PROFILE_NAMES as readonly string[]).includes(s);
}

export function getAllowPrefixesForProfile(name: string): string[][] | null {
  if (!isWpCliProfileName(name)) {
    return null;
  }
  return WP_CLI_PRESETS[name].map((p) => [...p]);
}
