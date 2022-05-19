# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This changelog format was introduced in NAV 5.4.0. Older changelogs can be
found in the [HISTORY](HISTORY) file.

## [Unreleased]

## Changed

- The changelog format has changed from the legacy format into one based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- [#1154](https://github.com/Uninett/nav/issues/1154) Transceivers are no longer classed as modules
- [#2366](https://github.com/Uninett/nav/issues/2366) Generate more secure API tokens
- [#2367](https://github.com/Uninett/nav/pull/2367) Change Uninett to Sikt in footer and faq
- [#2403](https://github.com/Uninett/nav/pull/2403) Upgrade to napalm 3.4.1

## Added

- [#2107](https://github.com/Uninett/nav/issues/2107) Support more recent AKCP MIBs
- [#2342](https://github.com/Uninett/nav/issues/2342) Temperatures should be logged from Juniper devices
- [#2347](https://github.com/Uninett/nav/issues/2347) Report does not take comma separated rooms with wildcard.
- [#2357](https://github.com/Uninett/nav/issues/2357) Juniper VLAN interfaces are not properly associated with their VLANs
- [#2359](https://github.com/Uninett/nav/issues/2359) Log memory usage on Juniper devices
- [#2368](https://github.com/Uninett/nav/pull/2368) Document NAV's various command line utilities
- [#2371](https://github.com/Uninett/nav/issues/2371) Write a contrib script that serves as a proof-of-concept of such an integration with the ISC DHCP server.

## Fixed

- [#1016](https://github.com/Uninett/nav/issues/1016) geomap link to this configuration results in alert
- [#2156](https://github.com/Uninett/nav/issues/2156) Optimize SeedDB prefix listing queries
- [#2334](https://github.com/Uninett/nav/issues/2334) My stuff Quick links, unable to delete link
- [#2362](https://github.com/Uninett/nav/issues/2362) Unfriendly RPC error reports in Portadmin
- [#2379](https://github.com/Uninett/nav/issues/2379) Get rid of warning: CacheKeyWarning: Cache key contains characters that will cause errors if used with memcached
- [#2381](https://github.com/Uninett/nav/issues/2381) Get rid of warning: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated
- [#2382](https://github.com/Uninett/nav/issues/2382) Get rid of warning: django.contrib.postgres.fields.JSONField is deprecated. Support for it (except in historical migrations) will be removed in Django 4.0.
- [#2385](https://github.com/Uninett/nav/issues/2385) [BUG] Room image thumbnails are rotated incorrectly
- [#2396](https://github.com/Uninett/nav/pull/2396) Change import of JSONField
- [#2399](https://github.com/Uninett/nav/pull/2399) Migrate to django 3.2 for docs
- [#2400](https://github.com/Uninett/nav/pull/2400) Optimize SeedDB room listing queries
- [#2401](https://github.com/Uninett/nav/pull/2401) Optimize SeedDB netboxtype listing queries
- [#2402](https://github.com/Uninett/nav/pull/2402) Optimize SeedDB vlan listing queries
- [#2407](https://github.com/Uninett/nav/pull/2407) Fix broken deserialization of Rack data
- [#2416](https://github.com/Uninett/nav/pull/2416) Remove unnecessary quotation marks
- [#2417](https://github.com/Uninett/nav/pull/2417) Set stateless state in EventFactory notify

## Removed

- [#2319](https://github.com/Uninett/nav/issues/2319) Get rid of "six" and support for Python 2
