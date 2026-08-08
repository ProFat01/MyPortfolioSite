/**
 * analytics/track.js
 * Tiny, dependency-free click beacon. Fires on any element with a
 * [data-track-event] attribute; never blocks the click's default
 * action (following a link, downloading a file, etc.) and never
 * throws — a tracking failure must never affect the visitor.
 *
 * Attributes read from the clicked element:
 *   data-track-event   required — one of the server's known event types
 *   data-track-project  optional — a Project id (for project_click / presentation_download)
 */
(function () {
  var ENDPOINT = '/analytics/track/';

  function send(eventType, projectId, path) {
    var payload = JSON.stringify({
      event_type: eventType,
      project_id: projectId || null,
      path: path,
    });

    try {
      if (navigator.sendBeacon) {
        var blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon(ENDPOINT, blob);
        return;
      }
    } catch (e) {
      // fall through to fetch
    }

    try {
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      }).catch(function () {});
    } catch (e) {
      // Tracking is best-effort only — never surface an error to the visitor.
    }
  }

  document.addEventListener('click', function (event) {
    var el = event.target.closest('[data-track-event]');
    if (!el) return;
    send(el.getAttribute('data-track-event'), el.getAttribute('data-track-project'), window.location.pathname);
  });
})();
