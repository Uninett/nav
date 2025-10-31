=================================================================
Migrating DHCP stats collected with NAV 5.14.x through NAV 5.16.x
=================================================================

We've provided a Bash script below that migrates DHCP stats collected with NAV
5.14.x through NAV 5.16.x to the locations expected and used by NAV 5.17.0 and
above. Run the script on the same machine as the machine running your
Graphite/Carbon backend and hence from where your Whisper timeseries data files
are reachable.

Before running the script, you should at the very minimum read its comments and
also replace the path in the highlighted line with the path to the root of where
your Whisper files are stored. (This could for example be
``/var/lib/graphite/whisper``. To be assured that this is the correct path and
that this script will have any effect, you could then verify that
``/var/lib/graphite/whisper/nav/dhcp`` also exists.) As always when making
automated changes to a file tree, you should take a backup of the file tree
before proceeding.

.. code-block:: bash
  :emphasize-lines: 12

  #!/bin/bash

  shopt -s nullglob

  # Renames the paths under nav.dhcp from the way paths are named in NAV
  # 5.14.x through NAV 5.16.x to the way paths are named in NAV 5.17.0 and
  # above

  # $WHISPER_ROOT should point to the root of the whisper database's file tree.
  # The user running this script must have write-access to this file tree.
  # You should take a backup of this file tree before running this script.
  WHISPER_ROOT="/path/to/whisper/data/root"

  if ! [[ -d "$WHISPER_ROOT/nav/dhcp" ]]; then
      echo "Error: Could not find directory $WHISPER_ROOT/nav/dhcp" >&2
      echo "No paths to rename." >&2
      exit 2
  fi

  pushd "$WHISPER_ROOT" 1>/dev/null 2>/dev/null || exit 1
  for path in nav/dhcp/*/pool/*/*/*/*/*; do
      if ! [[ -f "$path" ]]; then
          continue
      fi
      if [[ -h "$path" ]]; then
          continue
      fi
      IFS='/' read -ra parts <<< "$path"
      ip_version="${parts[2]}"
      server_name="${parts[4]}"
      group_name="${parts[5]}"
      first_ip="${parts[6]}"
      last_ip="${parts[7]}"
      metric_name="${parts[8]}"
      if [[ "$group_name" = "pool-${first_ip}-${last_ip}" ]]; then
          new_path="nav/dhcp/servers/${server_name}/range/special_groups/standalone/${ip_version}/${first_ip}/${last_ip}/${metric_name}"
          new_dir="nav/dhcp/servers/${server_name}/range/special_groups/standalone/${ip_version}/${first_ip}/${last_ip}/"
      else
          new_path="nav/dhcp/servers/${server_name}/range/custom_groups/${group_name}/${ip_version}/${first_ip}/${last_ip}/${metric_name}"
          new_dir="nav/dhcp/servers/${server_name}/range/custom_groups/${group_name}/${ip_version}/${first_ip}/${last_ip}/"
      fi
      mkdir -p "$new_dir"
      if [[ -f "$new_path" ]]; then
          if whisper-fill "$path" "$new_path"; then
              # unlink "$path"  # Uncomment to unlink old path
              true
          fi
      else
          if ln --verbose "$path" "$new_path"; then
              # unlink "$path"  # Uncomment to unlink old path
              true
          fi
      fi
  done
  # find "nav/dhcp" -depth -empty -type d -delete  # Uncomment to remove any resulting empty directories
  popd 1>/dev/null 2>/dev/null || exit 1
