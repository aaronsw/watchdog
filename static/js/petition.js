$(document).ready( function(){

strip = function(s) { return s.replace(/^\s+/, '').replace(/\s+$/, ''); }
remove_punctuation = function(s) { return s.replace(/[^a-z0-9-]/g,''); }

var ptitle_event = function fillURL(){
    if(! $('#pid').attr('readonly')){
        url = strip(this.value).toLowerCase().replace(/\s+/g, '-');
        url = remove_punctuation(url);
        $('#pid').val(url);
    }    
    return;
}

$('#ptitle').change(ptitle_event);
$('#ptitle').blur(ptitle_event);

$('#pid').change( function checkID(){
    $.post('/c/checkID', {pid: strip(this.value)},
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
});
