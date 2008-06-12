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

?>
