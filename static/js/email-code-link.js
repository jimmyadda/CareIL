(function () {
  var field = document.querySelector('[data-email-code]');
  var match = /^#code=([A-Za-z0-9]{6})$/.exec(window.location.hash);
  if (!field || !match) return;
  field.value = match[1].toUpperCase();
  // Keep the one-time code out of browser history and any subsequent copied URL.
  window.history.replaceState(null, '', window.location.pathname + window.location.search);
})();
