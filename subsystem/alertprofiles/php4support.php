<?php

// Parameterized queries for PHP < 5.1
// Allows use of pg_query_params() in the project
if (!function_exists('pg_query_params')) {
	function pg_query_params__callback($at) {
		global $pg_query_params__parameters;
		return $pg_query_params__parameters[$at[1] -1];
	}


	function pg_query_params($db, $query, $params) {
		global $pg_query_params__parameters;

		// Escape paramteres according to these rules:
		//   - Strings: Use pg_escape_string()
		//   - Integers: Do not escape at all
		//   - The "null" value: Add quotes
		foreach ($params as $k => $v) {
			if (is_null($v))
				$params[$k] = 'null';
			elseif (is_int($v))
				$params[$k] = $v;
			else
				$params[$k] = "'".pg_escape_string($v)."'";
		}
		$pg_query_params__parameters = $params;

		$query = preg_replace_callback('/\$(\d+)/', 'pg_query_params__callback', $query);
		return pg_query($db, $query);
	}
}

// Async parameterized queries for PHP < 5.1
if (!function_exists('pg_send_query_params')) {
	function pg_send_query_params__callback($at) {
		global $pg_send_query_params__parameters;
		return $pg_send_query_params__parameters[$at[1] -1];
	}

	function pg_send_query_params($db, $query, $params) {
		global $pg_send_query_params__parameters;

		foreach ($params as $k => $v) {
			if (is_null($v))
				$params[$k] = 'null';
			elseif (is_int($v))
				$params[$k] = $v;
			else
				$params[$k] = "'".pg_escape_string($v)."'";
		}
		$pg_send_query_params__parameters = $params;

		$query = preg_replace_callback('/\$(\d+)/', 'pg_send_query_params__callback', $query);
		return pg_send_query($db, $query);
	}
}

// pg_query() was once known as pg_exec()
if (!function_exists('pg_query')) {
	function pg_query($param1, $param2) {
		return pg_exec($param1, $param2);
	}
}

// pg_num_rows() was once named pg_numrows()
if (!function_exists('pg_num_rows')) {
	function pg_num_rows($result) {
		return pg_numrows($result);
	}
}

// pg_escape_string() was introduced in PHP 4.2, use addslashes if
// pg_escape_string() is not available
if (!function_exists('pg_escape_string')) {
	function pg_escape_string($string) {
		return addslashes($string);
	}
}

// pg_fetch_result() was once called pg_result()
if (!function_exists('pg_fetch_result')) {
	function pg_fetch_result($result, $row, $field) {
		if (!isset($field)) {
			$field = $row;
			$row = 0;
		}
		return pg_result($result, $row, $field);
	}
}

?>
