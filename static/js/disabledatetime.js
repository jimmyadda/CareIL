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
      var raw = part && part.appointment_date ? part.appointment_date : part;
      var value = String(raw || '').trim();
      var match = value.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2})/);
      if (match) return match[1] + '-' + match[2] + '-' + match[3] + ':' + pad(parseInt(match[4], 10));
      var parsed = new Date(value);
      if (!isNaN(parsed.getTime())) {
        return parsed.getFullYear() + '-' + pad(parsed.getMonth() + 1) + '-' +
          pad(parsed.getDate()) + ':' + pad(parsed.getHours());
      }
      return value;
    }).filter(function (value) { return /^\d{4}-\d{2}-\d{2}:\d{2}$/.test(value); });
}

function normalizeAppointmentDateValue(value) {
  var normalized = String(value || '').trim().replace('T', ' ');
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(normalized)) normalized += ':00';
  return normalized;
}

function bindAppointmentPickerButtons(scope) {
  var $scope = window.jQuery(scope || document);
  $scope.off('click.bookingPicker keydown.bookingPicker', '.open-appointment-picker')
    .on('click.bookingPicker keydown.bookingPicker', '.open-appointment-picker', function (event) {
      if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      var $input = window.jQuery(this).closest('.appointment-date-group').find('.form_datetime').first();
      if ($input.data('datetimepicker')) $input.datetimepicker('show');
      else $input.trigger('focus');
    });
}

window.jQuery(function () { bindAppointmentPickerButtons(document); });

function appointmentSlotKey(date) {
  return date.getUTCFullYear() + '-' + pad(date.getUTCMonth() + 1) + '-' +
    pad(date.getUTCDate()) + ':' + pad(date.getUTCHours());
}

function attachBookedSlotGuard(input, disabletime) {
  var $input = window.jQuery(input);
  var disabledSlots = new Set(changearrformat(disabletime));
  var reservedDates = new Set(Array.from(disabledSlots).map(function (slot) {
    return String(slot).slice(0, 10);
  }));

  function selectedPickerDate(picker) {
    // This datepicker updates viewDate when a day is selected, while `date`
    // still contains the old value until an hour is chosen.
    return picker && (picker.viewDate || picker.date);
  }

  function dateKey(date) {
    return date.getUTCFullYear() + '-' + pad(date.getUTCMonth() + 1) + '-' + pad(date.getUTCDate());
  }

  function markBookedDays() {
    var picker = $input.data('datetimepicker');
    var visibleDate = selectedPickerDate(picker);
    if (!picker || !picker.picker || !visibleDate) return;
    var viewYear = visibleDate.getUTCFullYear();
    var viewMonth = visibleDate.getUTCMonth();
    picker.picker.find('.datetimepicker-days td.day').each(function () {
      var $day = window.jQuery(this);
      var year = viewYear;
      var month = viewMonth;
      if ($day.hasClass('old')) {
        month -= 1;
        if (month < 0) { month = 11; year -= 1; }
      } else if ($day.hasClass('new')) {
        month += 1;
        if (month > 11) { month = 0; year += 1; }
      }
      var key = year + '-' + pad(month + 1) + '-' + pad(parseInt($day.text(), 10));
      var reserved = reservedDates.has(key);
      $day.toggleClass('has-booking', reserved)
        .attr('title', reserved ? 'This day has booked or requested appointments' : '');
    });
  }

  function markBookedHours(forDate) {
    var picker = $input.data('datetimepicker');
    if (!picker || !picker.picker) return;
    var selectedDate = forDate || $input.data('bookedSlotsSelectedDate') || selectedPickerDate(picker);
    if (!selectedDate || isNaN(selectedDate.getTime())) return;
    var datePrefix = dateKey(selectedDate);
    picker.picker.find('.datetimepicker-hours span.hour').each(function () {
      var hour = parseInt(window.jQuery(this).text(), 10);
      var booked = disabledSlots.has(datePrefix + ':' + pad(hour));
      window.jQuery(this).toggleClass('disabled booked-hour', booked)
        .attr('aria-disabled', booked ? 'true' : 'false')
        .attr('title', booked ? 'Unavailable' : '');
    });
  }

  function refreshBookingMarks() {
    markBookedDays();
    markBookedHours();
  }

  $input.off('.bookedSlots')
    .on('changeDay.bookedSlots', function (event) {
      if (event.date) $input.data('bookedSlotsSelectedDate', new Date(event.date.getTime()));
      window.setTimeout(function () { markBookedDays(); markBookedHours(event.date); }, 0);
      window.setTimeout(function () { markBookedHours(event.date); }, 30);
    })
    .on('show.bookedSlots changeMonth.bookedSlots changeYear.bookedSlots changeMode.bookedSlots',
      function () {
        window.setTimeout(refreshBookingMarks, 0);
        window.setTimeout(refreshBookingMarks, 30);
      })
    .on('changeHour.bookedSlots changeDate.bookedSlots', function (event) {
      var chosen = event.date;
      if (!chosen || !disabledSlots.has(appointmentSlotKey(chosen))) return;
      $input.val('').trigger('bookingSlotUnavailable');
      var picker = $input.data('datetimepicker');
      if (picker && picker.picker) picker.picker.find('.booked-slot-message').remove().end()
        .prepend('<div class="booked-slot-message" role="alert">This time is unavailable</div>');
    });
  var picker = $input.data('datetimepicker');
  if (picker && picker.picker) {
    var oldObserver = $input.data('bookedSlotsObserver');
    if (oldObserver) oldObserver.disconnect();
    var observer = new MutationObserver(function () {
      window.setTimeout(refreshBookingMarks, 0);
    });
    observer.observe(picker.picker[0], {childList: true, subtree: true});
    $input.data('bookedSlotsObserver', observer);

    var oldCapture = $input.data('bookedSlotsCapture');
    if (oldCapture && oldCapture.element) {
      oldCapture.element.removeEventListener('click', oldCapture.handler, true);
    }
    var pickerElement = picker.picker[0];
    var captureHandler = function (event) {
      var day = event.target.closest ? event.target.closest('.datetimepicker-days td.day') : null;
      if (day && !window.jQuery(day).hasClass('disabled')) {
        var base = selectedPickerDate(picker);
        var year = base.getUTCFullYear();
        var month = base.getUTCMonth();
        var $day = window.jQuery(day);
        if ($day.hasClass('old')) { month -= 1; if (month < 0) { month = 11; year -= 1; } }
        if ($day.hasClass('new')) { month += 1; if (month > 11) { month = 0; year += 1; } }
        $input.data('bookedSlotsSelectedDate', new Date(Date.UTC(year, month, parseInt($day.text(), 10))));
      }
      var target = event.target.closest ? event.target.closest('.booked-hour') : null;
      if (!target) return;
      event.preventDefault();
      event.stopImmediatePropagation();
    };
    pickerElement.addEventListener('click', captureHandler, true);
    $input.data('bookedSlotsCapture', {element: pickerElement, handler: captureHandler});
  }
  window.setTimeout(refreshBookingMarks, 0);
  window.setTimeout(refreshBookingMarks, 30);
}

function loadClinicAvailability() {
  return fetch('/api/availability', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) throw new Error('Availability could not be loaded');
      return response.json();
    })
    .catch(function (error) {
      console.warn('Clinic availability could not be loaded; using safe defaults:', error);
      return {days:[0,1,2,3,4], start:'08:00', end:'18:00', duration:60};
    });
}

function loadJewishHolidayDates() {
  var year = new Date().getFullYear();
  return fetch('/api/jewish-holidays?start_year=' + year + '&years=2', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) throw new Error('Holiday dates could not be loaded');
      return response.json();
    })
    .then(function (payload) { return payload.dates || []; })
    .catch(function (error) {
      console.warn('Jewish holidays could not be loaded in the picker:', error);
      return [];
    });
}

function availabilityPickerOptions(disabletime) {
  return Promise.all([loadClinicAvailability(), loadJewishHolidayDates()]).then(function (values) {
    var availability = values[0];
    var holidayDates = values[1];
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
      datesDisabled: holidayDates,
      autoclose: true,
      todayHighlight: true
    };
  });
}
