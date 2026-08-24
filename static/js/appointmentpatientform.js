$(function () {
    const patientId = new URLSearchParams(window.location.search).get('id');
    const $modal = $('#myModal');
    let bookedAppointmentTimes = [];

    function fullName(person, prefix) {
        return [person[prefix + '_first_name'], person[prefix + '_last_name']].filter(Boolean).join(' ');
    }
    function showError(message) {
        if ($.notify) $.notify(message, { status: 'danger' });
        else window.alert(message);
    }
    function loadOptions() {
        return $.when(
            $.getJSON('/doctorapi'),
            $.getJSON('/patientapi/' + encodeURIComponent(patientId)),
            $.getJSON('/appointmentapi')
        ).then(function (doctorResult, patientResult, appointmentResult) {
                const $doctors = $modal.find('#doctor_select').empty();
                const $patient = $modal.find('#patient_select').empty();
                (doctorResult[0] || []).forEach(function (doctor) {
                    $('<option>').val(doctor.doc_id).text(fullName(doctor, 'doc')).appendTo($doctors);
                });
                const patient = patientResult[0];
                $('<option>').val(patient.pat_id).text(fullName(patient, 'pat')).appendTo($patient);
                bookedAppointmentTimes = (appointmentResult[0] || []).map(function (item) {
                    return item.appointment_date;
                });
            });
    }
    function configureDatePicker() {
        if (!$.fn.datetimepicker) return;
        const disabled = typeof changearrformat === 'function' ? changearrformat(bookedAppointmentTimes) : bookedAppointmentTimes;
        $('.form_datetime').datetimepicker('remove').datetimepicker({
            format: 'yyyy-mm-dd hh:ii:00', minuteStep: 60, startDate: new Date(), initialDate: new Date(),
            onRenderHour: function (date) {
                if (typeof formatDate === 'function' && typeof pad === 'function' &&
                    disabled.indexOf(formatDate(date) + ':' + pad(date.getHours())) > -1) return ['disabled', 'booked-hour'];
                return [];
            }
        });
        if (typeof attachBookedSlotGuard === 'function') {
            attachBookedSlotGuard($('.form_datetime'), disabled);
        }
    }
    $('#addApp_pat_form').off('click').on('click.patientAppointment', function () {
        if (!patientId) return showError('Please select a patient first.');
        loadOptions().done(function () {
            $modal.modal('show').one('shown.bs.modal', configureDatePicker);
        }).fail(function () { showError('Could not load the appointment form. Please try again.'); });
    });
    $modal.find('#savethepatient').off('click').on('click.patientAppointment', function () {
        const $form = $modal.find('#detailform');
        if ($.fn.parsley) {
            const validation = $form.parsley(); validation.validate();
            if (!validation.isValid()) return;
        }
        const data = $form.serializeJSON ? $form.serializeJSON() : {};
        data.pat_id = patientId;
        $.ajax({url: '/appointmentapi', method: 'POST', contentType: 'application/json', data: JSON.stringify(data)})
            .done(function () {
                const message = sessionStorage.getItem('lang') === 'HE' ? 'פגישת טיפול נקבעה בהצלחה' : 'Appointment added successfully';
                if ($.notify) $.notify(message, {status: 'success'});
                $modal.modal('hide');
                window.setTimeout(function () { window.location.reload(); }, 350);
            })
            .fail(function (xhr) {
                const response = xhr.responseJSON;
                showError(response && response.error ? response.error : 'Could not add the appointment.');
            });
    });
});
