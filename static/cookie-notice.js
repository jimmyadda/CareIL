(function () {
  var notice = document.querySelector('[data-cookie-notice]');
  if (!notice) return;
  var key = 'careil-essential-cookie-notice-v1';
  try {
    if (window.localStorage.getItem(key) === 'acknowledged') return;
  } catch (error) {}
  notice.hidden = false;
  var button = notice.querySelector('[data-cookie-dismiss]');
  button.addEventListener('click', function () {
    try { window.localStorage.setItem(key, 'acknowledged'); } catch (error) {}
    notice.hidden = true;
  });
})();
