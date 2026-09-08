function formatDate(datestr)
{
    var date = new Date(datestr);
    var day = date.getDate(); 
    day = day>9?day:"0"+day;
    var month = date.getMonth()+1; month = month>9?month:"0"+month;
    return date.getFullYear()+"-"+month+"-"+day;
}

function pad(n)
{
  return n<10 ? '0'+n : n
}

function changearrformat(arr){
    return (arr || []).map(function(part) {
      var match = String(part).trim().match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2})/);
      return match ? match[1] + ':' + match[2] : String(part).trim();
    });
}

function appointmentSlotKey(date) {
  return date.getUTCFullYear() + '-' + pad(date.getUTCMonth() + 1) + '-' +
    pad(date.getUTCDate()) + ':' + pad(date.getUTCHours());
}

function attachBookedSlotGuard(input, disabletime) {
  var $input = window.jQuery(input);
  var disabledSlots = new Set(changearrformat(disabletime));

  function markBookedHours() {
    var picker = $input.data('datetimepicker');
    if (!picker || !picker.picker || !picker.viewDate) return;
    var datePrefix = picker.viewDate.getUTCFullYear() + '-' +
      pad(picker.viewDate.getUTCMonth() + 1) + '-' + pad(picker.viewDate.getUTCDate());
    picker.picker.find('.datetimepicker-hours span.hour').each(function () {
      var hour = parseInt(window.jQuery(this).text(), 10);
      var booked = disabledSlots.has(datePrefix + ':' + pad(hour));
      window.jQuery(this).toggleClass('disabled booked-hour', booked)
        .attr('aria-disabled', booked ? 'true' : 'false');
    });
  }

  $input.off('.bookedSlots').on(
    'show.bookedSlots changeDay.bookedSlots changeMonth.bookedSlots changeYear.bookedSlots changeMode.bookedSlots',
    function () { window.setTimeout(markBookedHours, 0); }
  );
  var picker = $input.data('datetimepicker');
  if (picker && picker.picker) {
    var oldObserver = $input.data('bookedSlotsObserver');
    if (oldObserver) oldObserver.disconnect();
    var observer = new MutationObserver(function () {
      window.setTimeout(markBookedHours, 0);
    });
    observer.observe(picker.picker[0], {childList: true, subtree: true});
    $input.data('bookedSlotsObserver', observer);

    var oldCapture = $input.data('bookedSlotsCapture');
    if (oldCapture && oldCapture.element) {
      oldCapture.element.removeEventListener('click', oldCapture.handler, true);
    }
    var pickerElement = picker.picker[0];
    var captureHandler = function (event) {
      var target = event.target.closest ? event.target.closest('.booked-hour') : null;
      if (!target) return;
      event.preventDefault();
      event.stopImmediatePropagation();
    };
    pickerElement.addEventListener('click', captureHandler, true);
    $input.data('bookedSlotsCapture', {element: pickerElement, handler: captureHandler});
  }
  window.setTimeout(markBookedHours, 0);
}

function loadClinicAvailability() {
  return fetch('/api/availability', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) throw new Error('Availability could not be loaded');
      return response.json();
    });
}

function availabilityPickerOptions(disabletime) {
  return loadClinicAvailability().then(function (availability) {
    var disabledSlots = new Set(changearrformat(disabletime));
    var startHour = parseInt(availability.start.split(':')[0], 10);
    var endHour = parseInt(availability.end.split(':')[0], 10);
    return {
      format: 'yyyy-mm-dd hh:ii:00',
      startDate: new Date(),
      minuteStep: availability.duration,
      initialDate: new Date(),
      hoursDisabled: Array.from({length: 24}, function (_, hour) { return hour; })
        .filter(function (hour) { return hour < startHour || hour >= endHour; }),
      daysOfWeekDisabled: Array.from({length: 7}, function (_, day) { return day; })
        .filter(function (day) { return availability.days.indexOf(day) === -1; }),
      onRenderHour: function (date) {
        if (disabledSlots.has(appointmentSlotKey(date))) {
          return ['disabled', 'booked-hour'];
        }
        return [];
      }
    };
  });
}
