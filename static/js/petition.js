$(document).ready( function(){

strip = function(s) { return s.replace(/^\s+/, '').replace(/\s+$/, ''); }
remove_punctuation = function(s) { return s.replace(/[^a-z0-9-]/g,''); }

var ptitle_event = function fillURL(){
    url = strip(this.value).toLowerCase().replace(/\s+/g, '-');
    url = remove_punctuation(url);
    $('#pid').val(url);
    $('#pid').change();
    return;
}

$('#ptitle').change(ptitle_event);

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

var tocongress_click = function() {
    if ($('#tocongress:checked').val()) {
        $('#tocongressform').show();
        $('#prefix').focus();
        $('#tocongresscheck').css('background-color', '#beb');
    } else {
        $('#tocongressform').hide()
        $('#tocongresscheck').css('background-color', '#ffc');
    }
}
$('#tocongress').click(tocongress_click);
tocongress_click();

var share_with_click = function() {
    if ($('#share_with:checked').val()) {
        $('#share_with_container').css('background-color', '#beb');
    } else {
        $('#share_with_container').css('background-color', '#ffc');
    }
}
$('#share_with').click(share_with_click);
share_with_click();

$('#ptitle').focus();
if ($('#tocongress:checked').val()) {
    $('#tocongressform').show();
    $('#tocongresscheck').css('background-color', '#ccebff');
}

}); // end of document.ready
