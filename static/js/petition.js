$(document).ready( function(){

strip = function(s) { return s.replace(/^\s+/, '').replace(/\s+$/, ''); }
remove_punctuation = function(s) { return s.replace(/[^a-z0-9-]/g,''); }

var ptitle_event = function fillURL(){
    url = strip(this.value).toLowerCase().replace(/\s+/g, '-');
    url = remove_punctuation(url);
    $('#pid').val(url);
    return;
}

$('#ptitle').change(ptitle_event);
$('#ptitle').blur(ptitle_event);

$('#pid').change( function checkID(){
    $.post('/c/verify', {pid: strip(this.value)},
         function(available){
            if (available == 'False'){
                msg = 'Address already exists, please choose a different one';
                $('#note_pid').html('<strong style="color:red">' + msg + '</strong>');
                $('#pid').focus();
                return false;
            }
            else { 
                $('#note_pid').html('');
                return true;
            }
        });
    });

$('#tocongress').click(function() {
    if ($('#tocongress:checked').val()) {
        $('#tocongressform').show();
        $('#prefix').focus();
        $('#tocongresscheck').css('background-color', '#ccebff');
    } else {
        $('#tocongressform').hide()
        $('#tocongresscheck').css('background-color', '#ffc');
    }
});

$('#ptitle').focus();
if ($('#tocongress:checked').val()) {
    $('#tocongressform').show();
    $('#tocongresscheck').css('background-color', '#ccebff');
}

}); // end of document.ready
