# Plan: replace Rickshaw with Chart.js

This document is the starting point for the migration. It assumes no other notes: everything a new session or developer needs to start is here, in the NAV repository, or in the issues it links to.

## Before you start: ask about the user test

The team (also known as Johnny-boy) planned a user test of the new graphs before the migration (guide: `tools/spike/brukertest.md`). **Ask the user whether the user test has been done, and what came out of it, before you do anything else.** Results may change the plan, for example whether to keep panning or how the legend works. Do not start Phase 2 until the user confirms.

## Background

- **#3967**, "Replace Rickshaw charting library with D3 v7", is the issue this work closes. It allows "a maintained lightweight alternative" to D3 v7. Use this number for the branch name, the changelog fragment and the `Closes` line.
- **#3907**, "Remove vendored D3 v3 by replacing or upgrading rickshaw", is the parent issue. Rickshaw is the only reason NAV still ships `libs/d3-3.5.5.min.js`.
- **#3409**, "Weird y-axis formatting of gauge dataplots", is a bug in the small sensor graphs that this work fixes.

Rickshaw is an unmaintained chart library on top of D3 v3. A spike on the branch `spike/rickshaw-replacement` compared Chart.js and uPlot on real NAV pages. **Chart.js was chosen**, mainly because stacked areas, panning and subtitles are configuration in Chart.js but custom code in uPlot. The findings are summarised in a comment on #3967.

## The spike branch

`spike/rickshaw-replacement` draws every Graphite graph with Rickshaw, uPlot or Chart.js, chosen with a URL parameter on the page:

- no parameter: Rickshaw, as today
- `?graphlib=chartjs`: Chart.js only
- `?graphlib=rickshaw&graphlib=chartjs`: both, side by side
- `?graphlib=all`: all three

The switch (`src/plugins/graphlib_switch.js`) and uPlot are spike-only. The branch is discarded after Phase 2 is merged.

Paths below are relative to `python/nav/web/` unless they start with `tools/`, `package.json` or `changelog.d/`.

### What to bring over to Phase 2

| What | Files on the spike branch |
|---|---|
| Chart.js and its plugins | `static/js/libs/chart-4.5.1.min.js`, `chartjs-adapter-moment-1.0.1.min.js`, `chartjs-plugin-zoom-2.2.0.min.js` |
| Hammer.js, only if panning is kept | `static/js/libs/hammer-2.0.8.min.js` |
| Loading | The Chart.js and `hammerjs` entries in `package.json` and `static/js/require_config.js` (paths and the `map` block), and `static/js/src/plugins/chartjs-helpers.js` |
| Loading test | `static/js/test/plugins/chartjs-loading-test.js` |
| Shared helpers | `static/js/src/plugins/graph-utils.js`, `static/js/test/plugins/graph-utils-test.js`, `static/js/test/div/graph-test.js`, and the import change in `static/js/src/plugins/rickshaw_graph.js` |
| The graph module | `static/js/src/plugins/timeseries_graph_chartjs.js`, renamed to `timeseries_graph.js` |
| Styles | `sass/nav/_timeseries_graph.scss` and its `@import "nav/timeseries_graph";` in `sass/nav.scss` |
| Backend, optional | `subtitle` in `python/nav/metrics/graphs.py`, and the VLAN title, subtitle and `valueformat='integer'` in `Vlan.get_graph_url` in `python/nav/models/manage.py` |

Leave behind: the uPlot library, its CSS (`sass/libs/uplot.css`) and its lines in `nav.scss`, `require_config.js` and `package.json`; `timeseries_graph_uplot.js`; `graphlib_switch.js` and its changes in `graphfetcher.js` and `sensor_controller.js`; and `tools/spike/`.

Two templates were changed from two columns to one, to fit three libraries side by side: the activity graphs in `templates/ipdevinfo/port-details.html` and the DHCP graphs in `templates/info/vlan/vlandetails.html`. With one library, decide again by looking at the pages.

### How to bring it over

Start the new branch from `master`. First cherry-pick the rename commit, so that `git log --follow` keeps the history of `graph-utils.js`. The final file differs too much from `rickshaw-utils.js` for git to detect the rename on its own.

```sh
git switch -c feature/replace-rickshaw-3967 master
git cherry-pick 3739a238ea   # Rename rickshaw-utils to graph-utils
```

Then take the final version of each file from the spike branch, and edit the shared files (`package.json`, `require_config.js`, `nav.scss`) by hand to leave uPlot out:

```sh
git checkout spike/rickshaw-replacement -- <path> ...
git diff master spike/rickshaw-replacement -- <path>   # to compare first
```

Most spike commits contain both libraries, so do not cherry-pick the others.

## What you need to know about Chart.js in NAV

- **RequireJS.** NAV's pages load RequireJS 2.0.4, but Karma uses a newer version, so a passing Karma test does not prove the pages load. Check in a browser too. The zoom plugin requires the module names `chart.js`, `chart.js/helpers` and `hammerjs`. RequireJS treats a name ending in `.js` as a file path, so the `map` block in `require_config.js` maps these names to NAV's paths.
- **Hammer.js** (2.0.8, last released in 2016) is only needed for panning. Without panning, map `hammerjs` to a stub module, `define(() => undefined)`, instead of shipping it. Hammer.js also stops page scrolling when you touch a graph. NAV is hardly used on phones, so this is not a priority.
- **Interface.** `new TimeSeriesGraph(container, data, url, minValue, options)`, the same call as the old `RickshawGraph`, plus `options`. The comment at the top of the module describes the arguments. `{compact: true}` gives a small graph for the sensor cards. The title, subtitle, unit and `valueformat` come from the container's `data-*` attributes or from the Graphite URL parameters.
- **Series metadata.** The backend puts metadata in the series alias: `"renderer=area;;color=#abc;;Name"`. `graph-utils.parseSeriesMeta()` reads it. Area series are stacked on each other and lines are not, as Rickshaw draws them. The VLAN and DHCP graphs depend on this.
- **Interaction.** Drag to zoom, double-click to reset, Shift-drag to pan. The legend is drawn on the canvas: a click toggles a series, and hovering highlights it.
- **Dashboard Graph widget.** It shows a PNG image drawn by Graphite, not Rickshaw, so it does not change. Graphite ignores the parameters only NAV's JavaScript uses, such as `subtitle` and `valueformat`.

## Decisions to make before or during Phase 2

1. **Panning:** keep it, and ship Hammer.js, or drop it and use the stub?
2. **Legend:** keep the canvas legend, which screen readers cannot read, or add an HTML legend through a Chart.js plugin?
3. **Backend changes:** bring over `subtitle` and `valueformat`?
4. **#3409 on the stable branch first?** Commit c454d2118e (February 2024) removed `@import 'sensors'` from `sass/nav/info_room.scss` and `sass/nav/navlets.scss`. Since then, `sass/nav/_sensors.scss` is never compiled, so the sensor cards have no width and the Rickshaw Y axis is drawn above the graph. Restoring the import may fix the bug on the stable branch. The relative `url(...)` paths to the jQuery UI images in that file must then be fixed too.

## Development environment

- Work in the NAV devcontainer (`doc/hacking/using-devcontainers.rst`). Graphite's web API is at `http://graphite:8000`, and Carbon (plaintext) at `graphite:2003`.
- For realistic pages, load a copy of a production database ("migrating_prod_db_to_dev" in the NAV documentation, and `tools/reset-db-from-remote.sh`).
- The copy has no Graphite data. The spike branch has three scripts that fill Graphite with mock data for one interface, one room's sensors, or one VLAN's prefixes. Run them from the Phase 2 branch without checking them out:

  ```sh
  git show spike/rickshaw-replacement:tools/spike/mock_port_metrics.py > /tmp/mock_port_metrics.py
  uv run python /tmp/mock_port_metrics.py <interface id>
  ```

  The same works for `mock_room_sensors.py <room id>` and `mock_vlan_prefixes.py <vlan id>`. The scripts write data up to the current time, so run them again before checking pages.
- Commands:
  - JS lint and tests: `tox -e javascript`. To run Karma directly, use `test/karma.conf.buildserver.js` from `python/nav/web/static/js`.
  - CSS: `make sassbuild`.
  - Web server: `uv run django-admin runserver`.
  - Functional tests: `tox run -e integration-py311-django52 -- tests/functional`.

## Conventions

- Each step below is one commit. Stop after each step so the user can review it.
- Commit subjects are at most 50 characters and complete "If applied, this commit will ...".
- New and rewritten JavaScript uses modern syntax (`const`/`let`, arrow functions, template literals) and no underscore.js. Leave existing underscore use alone in code you do not rewrite.
- Vendored JS files go in `static/js/libs/` with the version in the file name, and the version is listed in `package.json`.
- Do not put series names or titles into `innerHTML`. Use `textContent` or library options.
- Every pull request needs a towncrier fragment in `changelog.d/`, written for end users.

## Phase 2: the migration

### Step M1: Draw Graphite graphs with Chart.js

Suggested commit subject: `Draw Graphite graphs with Chart.js`. Bringing over the files above may be a commit of its own first.

1. In `static/js/src/plugins/graphfetcher.js`:
   - Import `plugins/timeseries_graph` in place of `plugins/rickshaw_graph`.
   - Look up `.nav-graph-container` in place of `.rickshaw-container`. If there is none, `graphfetcher` loads a PNG image instead; keep that.
   - Construct `new TimeSeriesGraph(...)` in place of `RickshawGraph`, and rename `self.rickshawgraph` to `self.graph`.
   - Leave the rest alone: the timeframe buttons, "Show trends", the image fallback and the "Add graph to dashboard" button.
2. In `static/js/src/ipdevinfo.js`, remove the unused dependency on `plugins/rickshaw_graph`.
3. Rename the class `rickshaw-container` to `nav-graph-container` in these templates:
   - `templates/ipdevinfo/`: `frag-port-metrics.html`, `frag-sensortable.html`, `frag-sysmetrics.html`, `poegroup-details.html`, `port-details-metrics-frag.html`, `port-details.html` and `sensor-details.html`
   - `templates/info/prefix/details.html` and `templates/info/vlan/vlandetails.html`
4. Remove the `local_rickshaw.css` `<link>` lines from `templates/ipdevinfo/base.html`, `templates/info/prefix/details.html` and `templates/info/vlan/vlandetails.html`.
5. In `tests/functional/ipdevinfo_test.py`, change the selector to `.graphitegraph .nav-graph-container`, and rename `rickshaw_containers` to `graph_containers`.
6. Add `changelog.d/3967.changed.md`, for example:
   > Time-series graphs are now drawn with the Chart.js library instead of the unmaintained Rickshaw library. Drag across a graph to zoom in, and double-click to reset the zoom.
7. Check these pages by hand, with mock data: the ipdevinfo activity and metrics tabs, port details, sensor details, a PoE group, prefix details (DHCP graphs) and VLAN details. On each, check the timeframe buttons (no duplicate graphs, no console errors), "Show trends", the legend, hover values with units, negative values, gaps and window resizing. Then run the functional tests.

### Step M2: Draw sensor graphs with Chart.js (fixes #3409)

Suggested commit subject: `Draw sensor graphs with Chart.js`

1. In `static/js/src/plugins/sensor_controller.js`:
   - Replace the Rickshaw graph with `new TimeSeriesGraph(node, data, url, 'auto', {compact: true})`. The spike draws the sensor graphs this way already (see `drawCompactGraphs` in `graphlib_switch.js`).
   - Remove the RangeSlider, the Y axis node and the hover detail template if nothing else uses it (check with `git grep`).
   - Keep the 60-second update and the "last value" for the gauge.
2. In `static/js/resources/room/sensor.html`, remove `.rs-ynode` and `.rs-slidernode`.
3. In `sass/nav/_sensors.scss`, delete the `.rs-ynode`, `.rs-slidernode` and `.rickshaw_graph` rules. Keep the card rules (`.room-sensors`, `.room-sensor`), and make sure the file is imported again (decision 4).
4. Add `changelog.d/3409.fixed.md`, for example:
   > Fixed the Y axis of sensor graphs being drawn above the graph, or out of line with it.
5. Check the room "Environment sensors" tab and a dashboard Sensor widget in both Firefox and Chromium. Wait for at least one 60-second update.

### Step M3: Remove Rickshaw and D3 v3

Suggested commit subject: `Remove Rickshaw and D3 v3`

1. Delete `static/js/libs/rickshaw.min.js`, `static/js/libs/d3-3.5.5.min.js`, `static/js/src/plugins/rickshaw_graph.js`, `static/js/resources/rickshawgraph/`, `sass/nav/rickshaw.scss` and `sass/nav/local_rickshaw.scss`.
2. Remove the `"d3": "libs/d3-3.5.5.min"` line from `require_config.js`. First confirm with `git grep -nE "['\"]d3['\"]" -- python/nav/web` that nothing requires `'d3'`. Also check `require_config_dev.js` and `build.js`.
3. Remove `@import "nav/rickshaw";` from `sass/nav.scss`.
4. In `graph-utils.js`, delete the functions marked "Rickshaw-only", and their tests in `test/div/graph-test.js`.
5. Replace "Rickshaw" with "NAV's time series graph (`plugins/timeseries_graph`)" in the docstrings of `python/nav/metrics/graphs.py` (`aliased_series`), `python/nav/dhcpstats/graph.py` and `Vlan.get_graph_url` in `python/nav/models/manage.py`.
6. Final checks: `git grep -i rickshaw` finds only `HISTORY` and `NOTES.rst`; `git grep d3-3.5.5` finds nothing; `tox -e javascript`, `make sassbuild` and the functional tests pass; every page from M1 and M2 loads with no 404s and no console errors.

## The pull request

- Target `master`. Say "Closes #3967" and "Fixes #3409", and refer to #3907 and the spike comment on #3967.
- Mention that the backend alias metadata format (`key=value;;name`) is unchanged.
- Mention the changes users will notice: drag-to-zoom replaces the preview slider, the new palette is safe for people with colour blindness, and the graphs are drawn on a canvas instead of in SVG.
- When Phase 2 is merged, delete the spike branch.
