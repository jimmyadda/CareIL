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

  $('#addpatient').off('click').on('click.appointmentPage', function () {
    $.when($.getJSON('/doctorapi'), $.getJSON('/patientapi'), $.getJSON('/appointmentapi'))
      .done(function (doctorResult, patientResult, appointmentResult) {
        const doctors = doctorResult[0] || [];
        const patients = patientResult[0] || [];
        bookedAppointmentTimes = (appointmentResult[0] || []).map(function (item) {
          return item.appointment_date;
        });
        const $doctor = $modal.find('#doctor_select').empty();
        const $patient = $modal.find('#patient_select').empty();
        doctors.forEach(function (item) {
          $('<option>').val(item.doc_id).text(nameOf(item, 'doc')).appendTo($doctor);
        });
        patients.forEach(function (item) {
          $('<option>').val(item.pat_id).text(nameOf(item, 'pat')).appendTo($patient);
        });
        $modal.modal('show').one('shown.bs.modal', function () {
          const disabled = changearrformat(bookedAppointmentTimes);
          availabilityPickerOptions(disabled).then(function (options) {
            if ($('.form_datetime').data('datetimepicker')) $('.form_datetime').datetimepicker('remove');
            $('.form_datetime').datetimepicker(options);
            attachBookedSlotGuard($('.form_datetime'), disabled);
          });
        });
      })
      .fail(function () { notifyError('Could not load the appointment form.'); });
  });

  $modal.find('#savethepatient').off('click').on('click.appointmentPage', function () {
    const $form = $modal.find('#detailform');
    const validation = $form.parsley();
    validation.validate();
    if (!validation.isValid()) return;
    const data = $form.serializeJSON();
    $.ajax({url:'/appointmentapi', method:'POST', contentType:'application/json', data:JSON.stringify(data)})
      .done(function () {
        if ($.notify) $.notify('Appointment added successfully', {status:'success'});
        $modal.modal('hide');
        window.setTimeout(function () { window.location.reload(); }, 350);
      })
      .fail(function (xhr) {
        notifyError((xhr.responseJSON && xhr.responseJSON.error) || 'Could not add the appointment.');
      });
  });
});
