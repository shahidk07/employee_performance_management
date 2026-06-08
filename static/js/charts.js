// D3.js Visualizations for EPMS Dashboards

$(document).ready(function() {
    // Only load charts if we are on a page that has chart containers
    if ($('#rating-chart').length || $('#attendance-chart').length || $('#project-chart').length || $('#dept-chart').length) {
        loadDashboardData();
    }
});

function loadDashboardData() {
    // Fetch data from Django API endpoint
    fetch('/api/dashboard-data/')
        .then(response => response.json())
        .then(data => {
            // Render visualizations
            if ($('#rating-chart').length) {
                renderRatingChart('#rating-chart', data.ratings);
            }
            if ($('#attendance-chart').length) {
                renderAttendanceChart('#attendance-chart', data.attendance);
            }
            if ($('#project-chart').length) {
                renderProjectChart('#project-chart', data.projects);
            }
            if ($('#dept-chart').length) {
                renderDeptChart('#dept-chart', data.departments);
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

// -------------------------------------------------------------
// D3.js Chart 1: Performance Rating Distribution (Bar Chart)
// -------------------------------------------------------------
function renderRatingChart(selector, data) {
    const container = d3.select(selector);
    const width = 450;
    const height = 280;
    const margin = { top: 20, right: 20, bottom: 40, left: 45 };

    // Clear existing
    container.html('');

    const svg = container.append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('width', '100%')
        .attr('height', '100%')
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const x = d3.scaleBand()
        .domain(data.map(d => `Star ${d.rating}`))
        .range([0, width - margin.left - margin.right])
        .padding(0.3);

    const y = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count) || 5])
        .nice()
        .range([height - margin.top - margin.bottom, 0]);

    // Color gradient for ratings
    const colorScale = d3.scaleOrdinal()
        .domain([1, 2, 3, 4, 5])
        .range(['#ef4444', '#f97316', '#eab308', '#3b82f6', '#22c55e']);

    // Tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'd3-tooltip');

    // Grid lines
    svg.append('g')
        .attr('class', 'grid')
        .attr('stroke', '#e2e8f0')
        .attr('stroke-opacity', 0.5)
        .call(d3.axisLeft(y)
            .tickSize(-width + margin.left + margin.right)
            .tickFormat('')
        );

    // Bars
    svg.selectAll('.bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'bar transition-all-300')
        .attr('x', d => x(`Star ${d.rating}`))
        .attr('y', height - margin.top - margin.bottom) // start animation from bottom
        .attr('width', x.bandwidth())
        .attr('height', 0)
        .attr('fill', d => colorScale(d.rating))
        .attr('rx', 4)
        .on('mouseover', function(event, d) {
            d3.select(this).attr('opacity', 0.85).attr('y', y(d.count) - 2);
            tooltip.style('opacity', 1)
                .html(`<strong>Reviews:</strong> ${d.count}`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mousemove', function(event) {
            tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).attr('opacity', 1).attr('y', d => y(d.count));
            tooltip.style('opacity', 0);
        })
        .transition()
        .duration(800)
        .attr('y', d => y(d.count))
        .attr('height', d => height - margin.top - margin.bottom - y(d.count));

    // X Axis
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.top - margin.bottom})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');

    // Y Axis
    svg.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('d')))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');
}

// -------------------------------------------------------------
// D3.js Chart 2: Monthly Attendance Trend (Line Chart)
// -------------------------------------------------------------
function renderAttendanceChart(selector, data) {
    const container = d3.select(selector);
    const width = 500;
    const height = 280;
    const margin = { top: 20, right: 30, bottom: 40, left: 45 };

    // Clear existing
    container.html('');

    const svg = container.append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('width', '100%')
        .attr('height', '100%')
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const x = d3.scalePoint()
        .domain(data.map(d => d.month))
        .range([0, width - margin.left - margin.right])
        .padding(0.2);

    const y = d3.scaleLinear()
        .domain([60, 100])
        .range([height - margin.top - margin.bottom, 0]);

    // Tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'd3-tooltip');

    // Grid lines
    svg.append('g')
        .attr('class', 'grid')
        .attr('stroke', '#e2e8f0')
        .attr('stroke-opacity', 0.5)
        .call(d3.axisLeft(y)
            .tickSize(-width + margin.left + margin.right)
            .tickFormat('')
        );

    // Line generator
    const line = d3.line()
        .x(d => x(d.month))
        .y(d => y(d.rate))
        .curve(d3.curveMonotoneX);

    // Area generator for gradient fill
    const area = d3.area()
        .x(d => x(d.month))
        .y0(height - margin.top - margin.bottom)
        .y1(d => y(d.rate))
        .curve(d3.curveMonotoneX);

    // Define Gradient
    const gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'area-gradient')
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '0%').attr('y2', '100%');

    gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', '#3b82f6')
        .attr('stop-opacity', 0.35);

    gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#3b82f6')
        .attr('stop-opacity', 0.0);

    // Draw area under line
    svg.append('path')
        .datum(data)
        .attr('fill', 'url(#area-gradient)')
        .attr('d', area);

    // Draw line
    const path = svg.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 3)
        .attr('d', line);

    // Line Animation
    const totalLength = path.node().getTotalLength();
    path.attr('stroke-dasharray', totalLength + ' ' + totalLength)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(1200)
        .attr('stroke-dashoffset', 0);

    // Draw Data Dots
    svg.selectAll('.dot')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'dot transition-all-300')
        .attr('cx', d => x(d.month))
        .attr('cy', d => y(d.rate))
        .attr('r', 5)
        .attr('fill', '#ffffff')
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 3)
        .on('mouseover', function(event, d) {
            d3.select(this).attr('r', 7).attr('fill', '#3b82f6');
            tooltip.style('opacity', 1)
                .html(`<strong>Attendance Rate:</strong> ${d.rate}%`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mousemove', function(event) {
            tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).attr('r', 5).attr('fill', '#ffffff');
            tooltip.style('opacity', 0);
        });

    // Axes
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.top - margin.bottom})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');

    svg.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => d + '%'))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');
}

// -------------------------------------------------------------
// D3.js Chart 3: Project Status Distribution (Donut Chart)
// -------------------------------------------------------------
function renderProjectChart(selector, data) {
    const container = d3.select(selector);
    const width = 380;
    const height = 280;
    const radius = Math.min(width, height) / 2 - 20;

    // Clear existing
    container.html('');

    // If data is empty, display message
    if (!data.length) {
        container.html('<div class="flex items-center justify-center h-full text-slate-400 font-medium">No projects to display</div>');
        return;
    }

    const svg = container.append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('width', '100%')
        .attr('height', '100%')
        .append('g')
        .attr('transform', `translate(${width / 2}, ${height / 2})`);

    const colorScale = d3.scaleOrdinal()
        .domain(['PLANNING', 'ACTIVE', 'COMPLETED', 'ON_HOLD'])
        .range(['#64748b', '#3b82f6', '#10b981', '#f59e0b']);

    const pie = d3.pie()
        .value(d => d.count)
        .sort(null);

    const arc = d3.arc()
        .innerRadius(radius * 0.55)
        .outerRadius(radius);

    const outerArc = d3.arc()
        .innerRadius(radius * 1.05)
        .outerRadius(radius * 1.05);

    const tooltip = d3.select('body').append('div')
        .attr('class', 'd3-tooltip');

    const arcs = svg.selectAll('.arc')
        .data(pie(data))
        .enter()
        .append('g')
        .attr('class', 'arc');

    // Draw slices
    arcs.append('path')
        .attr('fill', d => colorScale(d.data.status))
        .attr('d', arc)
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 2)
        .on('mouseover', function(event, d) {
            d3.select(this).transition().duration(200).attr('d', d3.arc().innerRadius(radius * 0.55).outerRadius(radius * 1.05));
            tooltip.style('opacity', 1)
                .html(`<strong>${d.data.status.replace('_', ' ')}:</strong> ${d.data.count} projects`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mousemove', function(event) {
            tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).transition().duration(200).attr('d', arc);
            tooltip.style('opacity', 0);
        })
        .transition()
        .duration(800)
        .attrTween('d', function(d) {
            const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
            return function(t) {
                return arc(interpolate(t));
            };
        });

    // Add labels dynamically if space permits
    arcs.append('text')
        .attr('transform', d => `translate(${arc.centroid(d)})`)
        .attr('dy', '.35em')
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', '#ffffff')
        .text(d => d.data.count > 0 ? d.data.count : '');
}

// -------------------------------------------------------------
// D3.js Chart 4: Department Employee Count (Horizontal Bar Chart)
// -------------------------------------------------------------
function renderDeptChart(selector, data) {
    const container = d3.select(selector);
    const width = 450;
    const height = 280;
    const margin = { top: 20, right: 30, bottom: 30, left: 100 };

    // Clear existing
    container.html('');

    // If data is empty
    if (!data.length) {
        container.html('<div class="flex items-center justify-center h-full text-slate-400 font-medium">No department data to display</div>');
        return;
    }

    const svg = container.append('svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('width', '100%')
        .attr('height', '100%')
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const y = d3.scaleBand()
        .domain(data.map(d => d.department))
        .range([0, height - margin.top - margin.bottom])
        .padding(0.35);

    const x = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.count) || 5])
        .nice()
        .range([0, width - margin.left - margin.right]);

    const tooltip = d3.select('body').append('div')
        .attr('class', 'd3-tooltip');

    // Horizontal grid lines
    svg.append('g')
        .attr('class', 'grid')
        .attr('stroke', '#e2e8f0')
        .attr('stroke-opacity', 0.5)
        .call(d3.axisBottom(x)
            .tickSize(height - margin.top - margin.bottom)
            .tickFormat('')
        );

    // Bars
    svg.selectAll('.bar')
        .data(data)
        .enter()
        .append('rect')
        .attr('class', 'bar transition-all-300')
        .attr('y', d => y(d.department))
        .attr('x', 0)
        .attr('height', y.bandwidth())
        .attr('width', 0) // start animation from left
        .attr('fill', '#3b82f6')
        .attr('rx', 3)
        .on('mouseover', function(event, d) {
            d3.select(this).attr('fill', '#2563eb');
            tooltip.style('opacity', 1)
                .html(`<strong>Employees:</strong> ${d.count}`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mousemove', function(event) {
            tooltip.style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).attr('fill', '#3b82f6');
            tooltip.style('opacity', 0);
        })
        .transition()
        .duration(800)
        .attr('width', d => x(d.count));

    // X Axis
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.top - margin.bottom})`)
        .call(d3.axisBottom(x).ticks(5).tickFormat(d3.format('d')))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');

    // Y Axis
    svg.append('g')
        .call(d3.axisLeft(y))
        .selectAll('text')
        .attr('font-weight', '500')
        .attr('fill', '#64748b');
}
