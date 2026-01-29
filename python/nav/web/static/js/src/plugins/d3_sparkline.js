/**
 * D3-based sparkline charts to replace jquery-sparkline
 *
 * Supports two chart types:
 * - line: Simple line chart with optional tooltips
 * - bullet: Horizontal bar showing value against max with optional color ranges
 *
 * Tooltip formatter signature:
 * - Line: tooltipFormatter({x, y, color}) - x/y are data point values
 * - Bullet: tooltipFormatter({$el, values}) - $el is jQuery-wrapped element, values is data array
 *
 * Note: Bullet tooltips use jQuery ($) for element wrapping
 */
define(function (require) {

    const d3 = require('d3v7');

    const defaults = {
        line: {
            width: 100,
            height: 20,
            strokeColor: '#00f',
            strokeWidth: 1,
            fillColor: 'rgba(0, 0, 255, 0.1)',
            tooltipFormatter: null
        },
        bullet: {
            width: null,  // null means 100%
            height: 20,
            performanceColor: 'lightsteelblue',
            rangeColors: ['#fff'],
            tooltipFormatter: null
        }
    };

    /**
     * Create a line sparkline
     * @param {HTMLElement|jQuery} container - Container element
     * @param {Array} data - Array of [x, y] pairs or just y values
     * @param {Object} options - Configuration options
     */
    function lineSparkline(container, data, options) {
        const el = container.jquery ? container[0] : container;
        if (!el) {
            return;
        }
        const opts = mergeOptions(defaults.line, options);

        // Clear any existing content
        el.innerHTML = '';

        if (!data || data.length === 0) {
            return;
        }

        // Normalize data to [x, y] pairs
        const normalizedData = normalizeLineData(data);

        // Handle percentage width (e.g. '100%') or use numeric value
        let width = opts.width;
        if (typeof opts.width === 'string' && opts.width.endsWith('%')) {
            width = el.clientWidth || 100;
        }
        const height = opts.height;

        const svg = d3.select(el).append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('display', 'block');

        const xExtent = d3.extent(normalizedData, d => d[0]);
        const yExtent = d3.extent(normalizedData, d => d[1]);

        // Ensure y range is not zero
        if (yExtent[0] === yExtent[1]) {
            yExtent[0] = yExtent[0] - 1;
            yExtent[1] = yExtent[1] + 1;
        }

        const x = d3.scaleLinear()
            .domain(xExtent)
            .range([1, width - 1]);

        const y = d3.scaleLinear()
            .domain(yExtent)
            .range([height - 2, 2]);

        const line = d3.line()
            .x(d => x(d[0]))
            .y(d => y(d[1]))
            .defined(d => d[1] !== null);

        // Draw fill area if fillColor is set
        if (opts.fillColor) {
            const area = d3.area()
                .x(d => x(d[0]))
                .y0(height)
                .y1(d => d[1] !== null ? y(d[1]) : height)
                .defined(d => d[1] !== null);

            svg.append('path')
                .datum(normalizedData)
                .attr('d', area)
                .attr('fill', opts.fillColor);
        }

        // Draw line
        svg.append('path')
            .datum(normalizedData)
            .attr('d', line)
            .attr('fill', 'none')
            .attr('stroke', opts.strokeColor)
            .attr('stroke-width', opts.strokeWidth);

        // Add tooltip functionality if formatter provided
        if (opts.tooltipFormatter) {
            addLineTooltip(svg, normalizedData, x, y, opts, width, height);
        }

        return svg;
    }

    /**
     * Create a bullet sparkline (horizontal bar with value indicator)
     * @param {HTMLElement|jQuery} container - Container element
     * @param {Array} data - Array: [null, value, ...ranges] - first null is ignored, second is value, rest are range boundaries
     * @param {Object} options - Configuration options
     */
    function bulletSparkline(container, data, options) {
        const el = container.jquery ? container[0] : container;
        if (!el) {
            return;
        }
        const opts = mergeOptions(defaults.bullet, options);

        // Clear any existing content
        el.innerHTML = '';

        if (!data || data.length < 2) {
            return;
        }

        // Parse bullet data: [null, value, max] or [null, value, threshold1, threshold2, ...]
        const value = data[1];
        const ranges = data.slice(2).filter(v => v !== null);

        if (ranges.length === 0) {
            return;
        }

        const max = Math.max(...ranges);

        let width = el.clientWidth || 100;
        if (opts.width && opts.width !== '100%') {
            width = opts.width;
        }
        const height = opts.height;

        const svg = d3.select(el).append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('display', 'block');

        const x = d3.scaleLinear()
            .domain([0, max])
            .range([0, width]);

        // Draw range backgrounds (from largest to smallest so colors layer correctly)
        const sortedRanges = ranges.slice().sort((a, b) => b - a);
        const rangeColors = opts.rangeColors.slice();

        // Extend colors if not enough provided
        while (rangeColors.length < sortedRanges.length) {
            rangeColors.push(rangeColors[rangeColors.length - 1] || '#ddd');
        }

        sortedRanges.forEach((rangeVal, i) => {
            svg.append('rect')
                .attr('x', 0)
                .attr('y', 0)
                .attr('width', x(rangeVal))
                .attr('height', height)
                .attr('fill', rangeColors[i]);
        });

        // Draw value bar
        if (value !== null) {
            const barHeight = height * 0.4;
            const barY = (height - barHeight) / 2;

            svg.append('rect')
                .attr('x', 0)
                .attr('y', barY)
                .attr('width', x(Math.min(value, max)))
                .attr('height', barHeight)
                .attr('fill', opts.performanceColor);
        }

        // Add tooltip if formatter provided
        if (opts.tooltipFormatter) {
            addBulletTooltip(svg, el, data, opts);
        }

        return svg;
    }

    /**
     * Normalize line data to [x, y] pairs
     */
    function normalizeLineData(data) {
        if (!Array.isArray(data[0])) {
            // Just y values, generate x indices
            return data.map((y, i) => [i, y]);
        }
        return data;
    }

    /**
     * Merge user options with defaults
     */
    function mergeOptions(defaults, options) {
        const result = { ...defaults };
        if (options) {
            Object.assign(result, options);
        }
        return result;
    }

    /**
     * Add tooltip functionality to line sparkline
     */
    function addLineTooltip(svg, data, xScale, yScale, opts, width, height) {
        const tooltip = createTooltip();

        // Create invisible overlay for mouse tracking
        const overlay = svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'transparent')
            .style('cursor', 'crosshair');

        // Add vertical line indicator
        const indicator = svg.append('line')
            .attr('y1', 0)
            .attr('y2', height)
            .attr('stroke', '#666')
            .attr('stroke-width', 1)
            .style('display', 'none');

        // Add dot indicator
        const dot = svg.append('circle')
            .attr('r', 3)
            .attr('fill', opts.strokeColor)
            .style('display', 'none');

        overlay.on('mousemove', function(event) {
            const mouse = d3.pointer(event, this);
            const xValue = xScale.invert(mouse[0]);

            // Find closest data point
            const closest = findClosestPoint(data, xValue);
            if (closest && closest[1] !== null) {
                const px = xScale(closest[0]);
                const py = yScale(closest[1]);

                indicator
                    .attr('x1', px)
                    .attr('x2', px)
                    .style('display', null);

                dot
                    .attr('cx', px)
                    .attr('cy', py)
                    .style('display', null);

                const tooltipData = {
                    x: closest[0],
                    y: closest[1],
                    color: opts.strokeColor
                };
                const html = opts.tooltipFormatter(tooltipData);
                showTooltip(tooltip, html, event);
            }
        });

        overlay.on('mouseout', () => {
            indicator.style('display', 'none');
            dot.style('display', 'none');
            hideTooltip(tooltip);
        });
    }

    /**
     * Add tooltip functionality to bullet sparkline
     */
    function addBulletTooltip(svg, el, data, opts) {
        const tooltip = createTooltip();

        svg.on('mouseover', (event) => {
            const tooltipData = {
                $el: $(el),
                values: data
            };
            const html = opts.tooltipFormatter(tooltipData);
            showTooltip(tooltip, html, event);
        });

        svg.on('mouseout', () => {
            hideTooltip(tooltip);
        });
    }

    /**
     * Find the closest data point to a given x value using binary search
     */
    function findClosestPoint(data, xValue) {
        if (data.length === 0) {
            return null;
        }
        if (data.length === 1) {
            return data[0];
        }

        let low = 0;
        let high = data.length - 1;

        while (high - low > 1) {
            const mid = Math.floor((low + high) / 2);
            if (data[mid][0] <= xValue) {
                low = mid;
            } else {
                high = mid;
            }
        }

        // Return the closer of the two adjacent points
        const distLow = Math.abs(data[low][0] - xValue);
        const distHigh = Math.abs(data[high][0] - xValue);
        return distLow <= distHigh ? data[low] : data[high];
    }

    /**
     * Create tooltip element
     */
    function createTooltip() {
        const existing = document.getElementById('d3-sparkline-tooltip');
        if (existing) {
            return existing;
        }

        const tooltip = document.createElement('div');
        tooltip.id = 'd3-sparkline-tooltip';
        tooltip.className = 'jqstooltip';  // Reuse existing sparkline tooltip styles
        tooltip.style.cssText = `position: fixed; display: none; z-index: 10000;
            background: #333; color: #fff; padding: 5px 10px; border-radius: 3px;
            font-size: 12px; pointer-events: none;`;
        document.body.appendChild(tooltip);
        return tooltip;
    }

    /**
     * Show tooltip at mouse position
     */
    function showTooltip(tooltip, html, event) {
        tooltip.innerHTML = html;
        tooltip.style.display = 'block';

        // Position near mouse
        let x = event.clientX + 10;
        let y = event.clientY + 10;

        // Keep on screen
        const rect = tooltip.getBoundingClientRect();
        if (x + rect.width > window.innerWidth) {
            x = event.clientX - rect.width - 10;
        }
        if (y + rect.height > window.innerHeight) {
            y = event.clientY - rect.height - 10;
        }

        tooltip.style.left = `${x}px`;
        tooltip.style.top = `${y}px`;
    }

    /**
     * Hide tooltip
     */
    function hideTooltip(tooltip) {
        tooltip.style.display = 'none';
    }

    // Export API
    return {
        line: lineSparkline,
        bullet: bulletSparkline
    };

});
