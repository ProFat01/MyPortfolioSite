/**
 * analytics/dashboard.js
 * Vanilla JS. Fetches /analytics/dashboard/data/ for the selected date
 * range and (re)renders the summary cards, tables, and Chart.js charts.
 * No page reload when switching ranges.
 */
(function () {
  var root = document.getElementById('analytics-dashboard');
  if (!root) return;

  var dataUrl = root.dataset.dataUrl;
  var rangeGroup = document.getElementById('analytics-range-group');
  var customForm = document.getElementById('analytics-custom-range');
  var startInput = document.getElementById('analytics-start-date');
  var endInput = document.getElementById('analytics-end-date');

  var charts = {};

  function getField(obj, path) {
    return path.split('.').reduce(function (acc, key) {
      return acc && acc[key] !== undefined ? acc[key] : undefined;
    }, obj);
  }

  function renderStats(data) {
    document.querySelectorAll('[data-field]').forEach(function (el) {
      var value = getField(data, el.dataset.field);
      if (value === undefined || value === null) {
        el.textContent = '0' + (el.dataset.suffix || '');
      } else {
        el.textContent = value + (el.dataset.suffix || '');
      }
    });
  }

  function renderTable(tableId, rows, rowRenderer) {
    var table = document.getElementById(tableId);
    var emptyEl = document.querySelector('[data-empty-for="' + tableId + '"]');
    if (!table) return;
    var tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    if (!rows || rows.length === 0) {
      table.style.display = 'none';
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }
    table.style.display = '';
    if (emptyEl) emptyEl.style.display = 'none';

    rows.forEach(function (row) {
      var tr = document.createElement('tr');
      tr.innerHTML = rowRenderer(row);
      tbody.appendChild(tr);
    });
  }

  function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = value === undefined || value === null ? '' : String(value);
    return div.innerHTML;
  }

  function destroyChart(key) {
    if (charts[key]) {
      charts[key].destroy();
      delete charts[key];
    }
  }

  function renderCharts(data) {
    if (typeof Chart === 'undefined') return; // Chart.js failed to load (e.g. offline) — tables still work.

    // Visits & Visitors over time (combined line chart)
    destroyChart('visitsOverTime');
    var visitsCanvas = document.getElementById('chart-visits-over-time');
    if (visitsCanvas) {
      var labels = (data.charts.visits_over_time || []).map(function (r) { return r.date; });
      charts.visitsOverTime = new Chart(visitsCanvas, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Visits',
              data: (data.charts.visits_over_time || []).map(function (r) { return r.visits; }),
              borderColor: '#17a2b8',
              backgroundColor: 'rgba(23,162,184,0.15)',
              tension: 0.3,
              fill: true,
            },
            {
              label: 'Unique Visitors',
              data: (data.charts.visitors_over_time || []).map(function (r) { return r.visitors; }),
              borderColor: '#6f42c1',
              backgroundColor: 'rgba(111,66,193,0.1)',
              tension: 0.3,
              fill: true,
            },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
      });
    }

    // Device breakdown (doughnut)
    destroyChart('deviceBreakdown');
    var deviceCanvas = document.getElementById('chart-device-breakdown');
    if (deviceCanvas) {
      var deviceRows = data.charts.device_breakdown || [];
      charts.deviceBreakdown = new Chart(deviceCanvas, {
        type: 'doughnut',
        data: {
          labels: deviceRows.map(function (r) { return r.device_type; }),
          datasets: [{
            data: deviceRows.map(function (r) { return r.count; }),
            backgroundColor: ['#17a2b8', '#6f42c1', '#fd7e14', '#adb5bd'],
          }],
        },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }

    // Most visited pages (horizontal bar)
    destroyChart('topPages');
    var pagesCanvas = document.getElementById('chart-top-pages');
    if (pagesCanvas) {
      var pageRows = data.charts.most_visited_pages || [];
      charts.topPages = new Chart(pagesCanvas, {
        type: 'bar',
        data: {
          labels: pageRows.map(function (r) { return r.path; }),
          datasets: [{ label: 'Visits', data: pageRows.map(function (r) { return r.count; }), backgroundColor: '#17a2b8' }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true } },
        },
      });
    }

    // Project views over time (bar)
    destroyChart('projectViews');
    var projectViewsCanvas = document.getElementById('chart-project-views');
    if (projectViewsCanvas) {
      var pv = data.projects.views_over_time || [];
      charts.projectViews = new Chart(projectViewsCanvas, {
        type: 'bar',
        data: {
          labels: pv.map(function (r) { return r.date; }),
          datasets: [{ label: 'Project clicks', data: pv.map(function (r) { return r.count; }), backgroundColor: '#fd7e14' }],
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
      });
    }
  }

  function renderTables(data) {
    renderTable('table-top-pages', data.most_visited_pages, function (r) {
      return '<td>' + escapeHtml(r.path) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
    renderTable('table-referrers', data.top_referrers, function (r) {
      return '<td>' + escapeHtml(r.referrer) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
    renderTable('table-browsers', data.browser_breakdown, function (r) {
      return '<td>' + escapeHtml(r.browser) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
    renderTable('table-os', data.os_breakdown, function (r) {
      return '<td>' + escapeHtml(r.operating_system) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
    renderTable('table-projects', data.projects.most_viewed, function (r) {
      return '<td>' + escapeHtml(r.project__title) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
    renderTable('table-downloads', data.projects.presentation_downloads, function (r) {
      return '<td>' + escapeHtml(r.project__title) + '</td><td class="text-end">' + escapeHtml(r.count) + '</td>';
    });
  }

  function load(range, startDate, endDate) {
    var url = dataUrl + '?range=' + encodeURIComponent(range || '7d');
    if (range === 'custom' && startDate && endDate) {
      url += '&start=' + encodeURIComponent(startDate) + '&end=' + encodeURIComponent(endDate);
    }
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        renderStats(data);
        renderTables(data);
        renderCharts(data);
      })
      .catch(function () {
        // Fail quietly — an admin-only dashboard glitch shouldn't throw errors at the visitor-facing site.
      });
  }

  rangeGroup.addEventListener('click', function (event) {
    var btn = event.target.closest('.analytics-range-btn');
    if (!btn) return;
    rangeGroup.querySelectorAll('.analytics-range-btn').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    load(btn.dataset.range);
  });

  customForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (!startInput.value || !endInput.value) return;
    rangeGroup.querySelectorAll('.analytics-range-btn').forEach(function (b) { b.classList.remove('active'); });
    load('custom', startInput.value, endInput.value);
  });

  load('7d');
})();
