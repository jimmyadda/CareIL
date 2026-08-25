$(function () {
  const $modal = $('#myModal');
  let bookedAppointmentTimes = [];

  function nameOf(item, prefix) {
    return [item[prefix + '_first_name'], item[prefix + '_last_name']].filter(Boolean).join(' ');
  }

  function notifyError(message) {
    if ($.notify) $.notify(message, {status: 'danger'});
    else window.alert(message);
  }

  function language() {
    return sessionStorage.getItem('lang') === 'HE' ? 'HE' : 'EN';
  }

  function text(en, he) {
    return language() === 'HE' ? he : en;
  }

  $('#addpatient').off('click').on('click.appointmentPage', function () {
    $.when($.getJSON('/patientapi'), $.getJSON('/appointmentapi'))
      .done(function (patientResult, appointmentResult) {
        const patients = patientResult[0] || [];
        bookedAppointmentTimes = (appointmentResult[0] || []).map(function (item) {
          return item.appointment_date;
        });
        const $patient = $modal.find('#patient_select').empty();
        $('<option>').val('').prop('disabled', true).prop('selected', true)
          .text(text('Select a client', 'בחרו מטופל')).appendTo($patient);
        patients.forEach(function (item) {
          $('<option>').val(item.pat_id).text(nameOf(item, 'pat')).appendTo($patient);
        });
        if (!patients.length) {
          $patient.empty().append($('<option>').val('').prop('disabled', true).prop('selected', true)
            .text(text('No clients available', 'אין מטופלים זמינים')));
          notifyError(text('Add a client before booking an appointment.', 'יש להוסיף מטופל לפני קביעת פגישה.'));
          return;
        }
        $modal.modal('show').one('shown.bs.modal', function () {
          const disabled = changearrformat(bookedAppointmentTimes);
          availabilityPickerOptions(disabled).then(function (options) {
            if ($('.form_datetime').data('datetimepicker')) $('.form_datetime').datetimepicker('remove');
            $('.form_datetime').datetimepicker(options);
            attachBookedSlotGuard($('.form_datetime'), disabled);
          });
        });
      })
      .fail(function () { notifyError(text('Could not load the appointment form.', 'לא ניתן לטעון את טופס הפגישה.')); });
  });

  $modal.find('#savethepatient').off('click').on('click.appointmentPage', function () {
    const $form = $modal.find('#detailform');
    const validation = $form.parsley();
    validation.validate();
    if (!validation.isValid()) return;
    const data = $form.serializeJSON();
    $.ajax({url:'/appointmentapi', method:'POST', contentType:'application/json', data:JSON.stringify(data)})
      .done(function () {
        if ($.notify) $.notify(text('Appointment added successfully', 'פגישת הטיפול נקבעה בהצלחה'), {status:'success'});
        $modal.modal('hide');
        window.setTimeout(function () { window.location.reload(); }, 350);
      })
      .fail(function (xhr) {
        notifyError((xhr.responseJSON && xhr.responseJSON.error) || text('Could not add the appointment.', 'לא ניתן לקבוע את הפגישה.'));
      });
  });
});
