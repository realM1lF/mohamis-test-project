<?php
/**
 * Plugin Name: OpenClaw Site Helper (MU)
 * Description: REST endpoints for OpenClaw agents (status, health, capabilities). Load from wp-content/mu-plugins/ (must-use).
 * Version: 0.2.0
 * Requires at least: 6.0
 * Requires PHP: 7.4
 *
 * @package OpenClaw_Site_Helper
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'OPENCLAW_SITE_HELPER_VERSION', '0.2.0' );

/**
 * Public route names (for status.features); keep in sync with register_rest_route paths.
 *
 * @return string[]
 */
function openclaw_site_helper_feature_list() {
	return array( 'status', 'health', 'me/capabilities' );
}

/**
 * @return bool
 */
function openclaw_site_helper_can_manage_options() {
	return current_user_can( 'manage_options' );
}

/**
 * @return bool
 */
function openclaw_site_helper_is_rest_user() {
	return is_user_logged_in();
}

/**
 * Count cron events whose timestamp is in the past (due/overdue).
 * Caps work to avoid pathological option sizes (see inline limit).
 *
 * @param int $max_hook_instances Max hook instances to scan (not timestamps).
 * @return int
 */
function openclaw_site_helper_count_overdue_crons( $max_hook_instances = 500 ) {
	if ( ! function_exists( '_get_cron_array' ) ) {
		return 0;
	}
	$crons = _get_cron_array();
	if ( empty( $crons ) || ! is_array( $crons ) ) {
		return 0;
	}
	$now   = time();
	$count = 0;
	$seen  = 0;
	foreach ( $crons as $timestamp => $hooks ) {
		if ( ! is_numeric( $timestamp ) || (int) $timestamp >= $now ) {
			continue;
		}
		foreach ( (array) $hooks as $hook => $instances ) {
			foreach ( (array) $instances as $sig => $data ) {
				++$count;
				++$seen;
				if ( $seen >= $max_hook_instances ) {
					return $count;
				}
			}
		}
	}
	return $count;
}

/**
 * Whitelisted PHP extensions (boolean map). No paths or versions.
 *
 * @return array<string, bool>
 */
function openclaw_site_helper_extension_flags() {
	$names = array( 'openssl', 'curl', 'gd', 'imagick', 'intl', 'mbstring', 'sodium' );
	$out     = array();
	foreach ( $names as $ext ) {
		$out[ $ext ] = extension_loaded( $ext );
	}
	return $out;
}

/**
 * Whether uploads base directory is writable (no path in API output).
 *
 * @return bool
 */
function openclaw_site_helper_upload_dir_writable() {
	$dir = wp_upload_dir();
	if ( ! empty( $dir['error'] ) ) {
		return false;
	}
	$basedir = isset( $dir['basedir'] ) ? $dir['basedir'] : '';
	if ( '' === $basedir || ! is_string( $basedir ) ) {
		return false;
	}
	return wp_is_writable( $basedir );
}

/**
 * Active plugins on current blog (count only).
 *
 * @return int
 */
function openclaw_site_helper_active_plugins_count() {
	$active = get_option( 'active_plugins', array() );
	return is_array( $active ) ? count( $active ) : 0;
}

add_action(
	'rest_api_init',
	function () {
		$namespace = 'openclaw-helper/v1';

		register_rest_route(
			$namespace,
			'/status',
			array(
				'methods'             => 'GET',
				'callback'            => function () {
					return rest_ensure_response(
						array(
							'ok'       => true,
							'helper'   => OPENCLAW_SITE_HELPER_VERSION,
							'features' => openclaw_site_helper_feature_list(),
							'wordpress' => get_bloginfo( 'version' ),
							'php'      => PHP_VERSION,
							'site_url' => get_site_url(),
						)
					);
				},
				'permission_callback' => 'openclaw_site_helper_can_manage_options',
			)
		);

		register_rest_route(
			$namespace,
			'/health',
			array(
				'methods'             => 'GET',
				'callback'            => function () {
					$wp_mem = defined( 'WP_MEMORY_LIMIT' ) ? WP_MEMORY_LIMIT : null;
					$data   = array(
						'ok'                    => true,
						'helper'                => OPENCLAW_SITE_HELPER_VERSION,
						'php_version'           => PHP_VERSION,
						'memory_limit_ini'      => ini_get( 'memory_limit' ),
						'wp_memory_limit'       => $wp_mem,
						'multisite'             => is_multisite(),
						'active_plugins_count'  => openclaw_site_helper_active_plugins_count(),
						'cron_overdue_count'    => openclaw_site_helper_count_overdue_crons(),
						'upload_dir_writable'   => openclaw_site_helper_upload_dir_writable(),
						'php_extensions'        => openclaw_site_helper_extension_flags(),
						'locale'                => get_locale(),
						'timezone_string'       => (string) get_option( 'timezone_string', '' ),
					);
					return rest_ensure_response( $data );
				},
				'permission_callback' => 'openclaw_site_helper_can_manage_options',
			)
		);

		register_rest_route(
			$namespace,
			'/me/capabilities',
			array(
				'methods'             => 'GET',
				'args'                => array(
					'check' => array(
						'description'       => 'Comma-separated capability names to test for the authenticated user.',
						'type'              => 'string',
						'required'          => false,
						'sanitize_callback' => 'sanitize_text_field',
					),
				),
				'callback'            => function ( WP_REST_Request $request ) {
					$user = wp_get_current_user();
					if ( ! $user || ! $user->ID ) {
						return new WP_Error(
							'openclaw_helper_no_user',
							'No authenticated user.',
							array( 'status' => 401 )
						);
					}
					$allcaps = is_array( $user->allcaps ) ? $user->allcaps : array();
					$true_caps = array();
					foreach ( $allcaps as $cap => $granted ) {
						if ( $granted ) {
							$true_caps[] = $cap;
						}
					}
					$true_caps = array_values( array_unique( $true_caps ) );
					sort( $true_caps, SORT_STRING );

					$out = array(
						'ok'     => true,
						'user_id' => (int) $user->ID,
						'capabilities' => $true_caps,
					);

					$check_raw = $request->get_param( 'check' );
					if ( is_string( $check_raw ) && '' !== trim( $check_raw ) ) {
						$parts = array_map( 'trim', explode( ',', $check_raw ) );
						$checks = array();
						foreach ( $parts as $cap ) {
							if ( '' === $cap || ! preg_match( '/^[a-z0-9_-]+$/i', $cap ) ) {
								continue;
							}
							$checks[ $cap ] = ! empty( $allcaps[ $cap ] );
						}
						$out['check_results'] = $checks;
					}

					return rest_ensure_response( $out );
				},
				'permission_callback' => 'openclaw_site_helper_is_rest_user',
			)
		);
	}
);
