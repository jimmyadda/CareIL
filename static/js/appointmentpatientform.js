$(function () {
    const patientId = new URLSearchParams(window.location.search).get('id');
    const $modal = $('#myModal');
    let bookedAppointmentTimes = [];

    function language() { return sessionStorage.getItem('lang') === 'HE' ? 'HE' : 'EN'; }
    function text(en, he) { return language() === 'HE' ? he : en; }
    function showError(message) {
        if ($.notify) $.notify(message, { status: 'danger' });
        else window.alert(message);
    }
    function loadOptions() {
        return $.getJSON('/appointmentapi').then(function (appointments) {
                bookedAppointmentTimes = (appointments || []).map(function (item) {
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
        if (!patientId) return showError(text('Please select a client first.', 'יש לבחור מטופל תחילה.'));
        loadOptions().done(function () {
            $modal.modal('show').one('shown.bs.modal', configureDatePicker);
        }).fail(function () { showError(text('Could not load the appointment form. Please try again.', 'לא ניתן לטעון את טופס הפגישה. נסו שוב.')); });
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
                const message = text('Appointment added successfully', 'פגישת טיפול נקבעה בהצלחה');
                if ($.notify) $.notify(message, {status: 'success'});
                $modal.modal('hide');
                window.setTimeout(function () { window.location.reload(); }, 350);
            })
            .fail(function (xhr) {
                const response = xhr.responseJSON;
                showError(response && response.error ? response.error : text('Could not add the appointment.', 'לא ניתן לקבוע את הפגישה.'));
            });
    });
});
