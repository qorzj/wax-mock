function clear_modal(opId) {
    $('#opid-input').val(opId)
    $('#modal-summary').html('...');
    $('#modal-desc').html('');
    $('#extra-input').val('');
    $('#modal-basic').html('');
    $.ajax({
        url: '/op/' + opId + '/example',
        method: 'GET',
        success: function (data) {
            $('#modal-summary').text(data.summary);
            $('#modal-desc').html(`<pre>${data.description || ''}</pre>`);
            $('#extra-input').val(data.extra || '');
            var basicHtml = '';
            var checkedBasic = (data.basic == null && data.all_example.length > 0) ? data.all_example[0] : data.basic;
            for (var stateBasic of data.all_example) {
                basicHtml += `<label>
                    <input value="${stateBasic}" name="state-basic" type="radio" ${stateBasic===checkedBasic?'checked':''} />
                    <span>${stateBasic}</span></label><br/>\n`;
            }
            $('#modal-basic').html(basicHtml);
        }
    });
}

function save_state() {
    var stateBasic = $('input[name=state-basic]:checked', '#modal-basic').val();
    if (stateBasic == null) return;
    $.ajax({
        url: '/op/state',
        method: 'POST',
        data: {
            'opId': $('#opid-input').val(),
            'basic': stateBasic,
            'extra': $('#extra-input').val()
        },
        success: function (data) {
        }
    });
}

function show_example(opId, resp_index, example_key) {
    $("#example-value").html("...");
    $.ajax({
        url: '/op/' + opId + '?show=json',
        method: 'GET',
        success: function (data) {
            $("#example-value").text(data.responses[resp_index]['examples'][example_key]);
        }
    });
}