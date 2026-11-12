#!/usr/bin/env bash
#
# Opens an sshuttle tunnel to NAV-monitored devices, through a remote host
# (typically the NAV server whose devices you want to poll from your own
# machine). Run with --help for usage.
#
# Uses sshuttle's tproxy method, as it is the only one that handles both IPv6
# and UDP (i.e. SNMP). That method needs root, which brings two wrinkles that
# this script takes care of:
#
# - tproxy needs policy routing to deliver marked packets back to the local
#   machine. The route and rule are added before starting, and removed on exit
#   (but only the ones this script added).
# - sshuttle starts ssh as root, so your ssh-agent socket, ssh config file and
#   known_hosts file are passed on explicitly, and the remote user name is
#   resolved from your ssh config up front.
#
# Known limitations:
# - Stop the tunnel with Ctrl-C. A SIGTERM to this script is only acted upon
#   once sshuttle exits.
# - Two simultaneous instances share the same routing table and mark. The
#   second leaves the routing alone, and the first removes it when it exits.
#
set -u

ROUTE_TABLE=100
FWMARK=0x1
# Must sit before any other rule that could capture the marked packets, such
# as a full-tunnel VPN rule.
RULE_PRIORITY=1
# The single source of truth for the routing this script manages. The ip(8)
# family flag and the add/del/show verbs are filled in where they are used.
ROUTE_SPEC=(local default dev lo table "$ROUTE_TABLE")
RULE_SPEC=(pref "$RULE_PRIORITY" fwmark "$FWMARK" lookup "$ROUTE_TABLE")

TOOLS_DIR=$(dirname "$(readlink -f "$0")")
SUBNETS_TOOL="$TOOLS_DIR/sshuttle-subnets.py"
# Distributions like Debian keep ip and iptables in sbin directories, which
# are not on a normal user's PATH
SBIN_DIRS=(/usr/local/sbin /usr/sbin /sbin)
# Entries like "-4 route" or "-6 rule", in the order they were added
ADDED_ROUTING=()
if [ -t 2 ]; then
  BOLD=$'\e[1m' YELLOW=$'\e[1;33m' RED=$'\e[1;31m' RESET=$'\e[0m'
else
  BOLD='' YELLOW='' RED='' RESET=''
fi
# Set by preflight_checks and resolve_remote
IP_BIN=
SSH_BIN=
SSHUTTLE_BIN=
SSHUTTLE_REMOTE=
SSH_SERVER_EXCLUDE=

main() {
  case "${1:-}" in
    -h | --help) usage; exit 0 ;;
    "") usage >&2; exit 2 ;;
    -*) die "The remote host must come first, got the option '$1'." \
      "Run with --help for usage." ;;
  esac
  local remote=$1
  shift
  preflight_checks $#

  local subnets=("$@")
  if [ ${#subnets[@]} -eq 0 ]; then
    local output
    output=$(subnets_from_nav) ||
      die "sshuttle-subnets.py failed (see its message above)"
    mapfile -t subnets <<<"$output"
  fi
  say "Will route these ${#subnets[@]} subnet(s) through $remote:"
  printf '      %s\n' "${subnets[@]}" >&2

  resolve_remote "$remote"
  check_ssh_agent
  acquire_sudo
  trap teardown_routing EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  setup_routing
  run_sshuttle "${subnets[@]}"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") REMOTE [SUBNET...]

Opens an sshuttle tunnel through REMOTE, routing traffic for the given
subnets through it. Linux only. Stop the tunnel with Ctrl-C.

  REMOTE  an ssh destination, [user@]host[:port], where host may be an alias
          from your ssh config. It is passed to sshuttle's -r option.
  SUBNET  subnets or addresses to route through the tunnel. If none are
          given, the default output of tools/sshuttle-subnets.py is used,
          i.e. the subnets of every netbox in the local NAV database.
EOF
}

preflight_checks() {
  local subnet_count=$1
  if [ "$(uname -s)" != Linux ]; then
    die "This script only works on Linux: it relies on sshuttle's tproxy" \
      "method and ip(8) policy routing, neither of which exists on" \
      "$(uname -s). Run sshuttle directly instead, and see its" \
      "documentation for the methods your OS supports."
  fi
  # Before 4.4, set -u treats empty arrays as unset variables
  if ((BASH_VERSINFO[0] * 100 + BASH_VERSINFO[1] < 404)); then
    die "This script needs bash 4.4 or newer, you have $BASH_VERSION."
  fi

  local problems=()
  require sshuttle "it creates the tunnel. Install your distribution's" \
    "sshuttle package, or 'pip install sshuttle'." || problems+=(sshuttle)
  require ssh "sshuttle uses it to reach the remote host. Install the" \
    "OpenSSH client." || problems+=(ssh)
  require sudo "sshuttle's tproxy method must run as root." ||
    problems+=(sudo)
  require ip "it sets up the policy routing that tproxy needs. Install" \
    "iproute2." || problems+=(ip)
  require iptables "sshuttle's tproxy method uses it for IPv4. Without" \
    "both iptables and ip6tables, sshuttle refuses to use tproxy." ||
    problems+=(iptables)
  require ip6tables "sshuttle's tproxy method uses it for IPv6. Without" \
    "both iptables and ip6tables, sshuttle refuses to use tproxy." ||
    problems+=(ip6tables)
  if [ "$subnet_count" -eq 0 ] && [ ! -x "$SUBNETS_TOOL" ]; then
    warn "Missing $SUBNETS_TOOL, which is needed to pick subnets when" \
      "none are given on the command line."
    problems+=(sshuttle-subnets.py)
  fi
  if [ ${#problems[@]} -gt 0 ]; then
    die "Cannot continue, missing: ${problems[*]}"
  fi

  # sudo may use a restricted PATH, so root is given absolute paths
  IP_BIN=$(find_cmd ip)
  SSH_BIN=$(find_cmd ssh)
  SSHUTTLE_BIN=$(find_cmd sshuttle)
}

require() {
  # Warns about a missing command, explaining why it is needed
  local cmd=$1
  shift
  find_cmd "$cmd" >/dev/null && return 0
  warn "'$cmd' was not found. It is needed because $*"
  return 1
}

find_cmd() {
  # Prints the absolute path of a command, also looking in sbin directories
  local cmd=$1 dir
  if type -P "$cmd"; then
    return 0
  fi
  for dir in "${SBIN_DIRS[@]}"; do
    if [ -x "$dir/$cmd" ]; then
      echo "$dir/$cmd"
      return 0
    fi
  done
  return 1
}

subnets_from_nav() {
  say "No subnets given, asking tools/sshuttle-subnets.py for the subnets" \
    "of all netboxes in the local NAV database..."
  "$SUBNETS_TOOL"
}

resolve_remote() {
  # Works out, as the invoking user, what ssh would do with the remote host
  # argument. ssh will run as root, and would otherwise default to logging in
  # as root.
  local remote=$1 user_part="" host_part=$1 host port=""
  if [[ $remote == *@* ]]; then
    user_part=${remote%@*}
    host_part=${remote##*@}
  fi
  if [[ $host_part == \[*\]* ]]; then # [IPv6 address]:port
    host=${host_part#[}
    host=${host%%]*}
    port=${host_part#*]}
    port=${port#:}
  elif [[ $host_part == *:*:* ]]; then # bare IPv6 address
    host=$host_part
  elif [[ $host_part == *:* ]]; then
    host=${host_part%:*}
    port=${host_part##*:}
  else
    host=$host_part
  fi

  local ssh_args=()
  [ -n "$user_part" ] && ssh_args+=(-l "${user_part%%:*}")
  [ -n "$port" ] && ssh_args+=(-p "$port")
  local config
  config=$("$SSH_BIN" -G "${ssh_args[@]}" "$host" 2>/dev/null) ||
    die "ssh could not make sense of the remote host '$remote'." \
      "Run 'ssh -G $host' to see why."
  local user hostname ssh_port
  user=$(ssh_option user <<<"$config")
  hostname=$(ssh_option hostname <<<"$config")
  ssh_port=$(ssh_option port <<<"$config")

  if [ -n "$user_part" ]; then
    SSHUTTLE_REMOTE=$remote
  else
    SSHUTTLE_REMOTE="$user@$host_part"
    say "Logging in as '$user', as your ssh config would."
  fi
  # sshuttle doesn't exclude its own ssh connection from the routed subnets,
  # which breaks the tunnel if the server is within one of them.
  if [[ $hostname == *:* ]]; then
    SSH_SERVER_EXCLUDE="[$hostname]:$ssh_port"
  else
    SSH_SERVER_EXCLUDE="$hostname:$ssh_port"
  fi
  if [ -n "$(ssh_option proxyjump <<<"$config")" ]; then
    warn "Your ssh config uses ProxyJump for this host. If the jump host is" \
      "within the routed subnets, the tunnel may break."
  fi
}

ssh_option() {
  # Reads the value of an option from `ssh -G` output on stdin
  awk -v key="$1" '$1 == key { print $2; exit }'
}

check_ssh_agent() {
  if [ -z "${SSH_AUTH_SOCK:-}" ]; then
    say "No ssh-agent found (SSH_AUTH_SOCK is not set), so ssh will ask for" \
      "your password on the remote host. To use an SSH key instead, load it" \
      "into your ssh-agent first: ssh runs as root, and cannot pick up the" \
      "key files in your own ~/.ssh directory."
  else
    say "Your ssh-agent ($SSH_AUTH_SOCK) will be handed to ssh running as" \
      "root, so it can use the keys loaded in it."
  fi
}

acquire_sudo() {
  say "sudo is needed for two things:"
  say "  1. adding a policy routing rule and route (table $ROUTE_TABLE," \
    "fwmark $FWMARK), which changes the kernel's routing configuration." \
    "Whatever this script adds is removed again when the tunnel closes;"
  say "  2. running sshuttle as root, as its tproxy method needs root to" \
    "set up iptables rules and transparent proxy sockets."
  say "Asking for your sudo password now, if sudo needs it:"
  sudo -v || die "Could not get sudo privileges"
}

setup_routing() {
  say "Setting up policy routing for sshuttle's tproxy method:"
  local family
  for family in -4 -6; do
    add_route "$family"
    add_rule "$family"
  done
}

add_route() {
  local family=$1
  if [ -n "$("$IP_BIN" "$family" route show table "$ROUTE_TABLE" \
    type local exact default dev lo 2>/dev/null)" ]; then
    say "  IPv${family#-}: the route is already present, leaving it be"
    return
  fi
  # Recorded before adding, so that an interrupt can't leak the route
  ADDED_ROUTING+=("$family route")
  run_root "$IP_BIN" "$family" route add "${ROUTE_SPEC[@]}" ||
    die "Could not add the IPv${family#-} route"
}

add_rule() {
  local family=$1
  if [ -n "$("$IP_BIN" "$family" rule show "${RULE_SPEC[@]}")" ]; then
    say "  IPv${family#-}: the rule is already present, leaving it be"
    return
  fi
  local elsewhere
  elsewhere=$("$IP_BIN" "$family" rule show fwmark "$FWMARK" table "$ROUTE_TABLE")
  if [ -n "$elsewhere" ]; then
    warn "IPv${family#-}: a rule for fwmark $FWMARK already exists at another" \
      "priority. Adding one at priority $RULE_PRIORITY as well, as rules at" \
      "lower priorities may be overridden by e.g. VPN rules: $elsewhere"
  fi
  ADDED_ROUTING+=("$family rule")
  run_root "$IP_BIN" "$family" rule add "${RULE_SPEC[@]}" ||
    die "Could not add the IPv${family#-} rule"
}

run_sshuttle() {
  local ssh_cmd=("$SSH_BIN")
  local config="$HOME/.ssh/config" known_hosts="$HOME/.ssh/known_hosts"
  [ -f "$config" ] && ssh_cmd+=(-F "$config")
  [ -f "$known_hosts" ] && ssh_cmd+=(-o "UserKnownHostsFile=$known_hosts")
  local ssh_cmdline
  # sshuttle splits its -e argument like a shell would
  printf -v ssh_cmdline '%q ' "${ssh_cmd[@]}"

  say "Starting sshuttle as root. Press Ctrl-C to close the tunnel."
  say "ssh reads your ssh config file and known_hosts file, but any '~' in" \
    "your config now means root's home directory. Keys come from your agent."
  run_root --preserve-env=SSH_AUTH_SOCK "$SSHUTTLE_BIN" --method tproxy \
    --tmark "$FWMARK" -e "${ssh_cmdline% }" -x "$SSH_SERVER_EXCLUDE" \
    -r "$SSHUTTLE_REMOTE" "$@"
  local status=$?
  say "sshuttle exited with status $status"
  return "$status"
}

teardown_routing() {
  # Finish the cleanup even if the user gets impatient
  trap '' INT TERM HUP
  [ ${#ADDED_ROUTING[@]} -gt 0 ] || return
  say "Removing the policy routing this script added." \
    "sudo may ask for your password again, if its cached credentials expired:"
  local family kind spec i
  # Remove in reverse order: rules before the routes they point to
  for ((i = ${#ADDED_ROUTING[@]} - 1; i >= 0; i--)); do
    read -r family kind <<<"${ADDED_ROUTING[i]}"
    if [ "$kind" = rule ]; then
      spec=("${RULE_SPEC[@]}")
    else
      spec=("${ROUTE_SPEC[@]}")
    fi
    run_root "$IP_BIN" "$family" "$kind" del "${spec[@]}" ||
      warn "Could not remove it. Try: sudo $IP_BIN $family $kind del ${spec[*]}"
  done
  ADDED_ROUTING=()
}

run_root() {
  # Runs a command with sudo, showing exactly what is run as root
  local shown
  printf -v shown ' %q' "$@"
  printf '%s==>%s   sudo%s\n' "$BOLD" "$RESET" "$shown" >&2
  sudo "$@"
}

say() {
  printf '%s==>%s %s\n' "$BOLD" "$RESET" "$*" >&2
}

warn() {
  printf '%s==> WARNING:%s %s\n' "$YELLOW" "$RESET" "$*" >&2
}

die() {
  printf '%s==> ERROR:%s %s\n' "$RED" "$RESET" "$*" >&2
  exit 1
}

main "$@"
