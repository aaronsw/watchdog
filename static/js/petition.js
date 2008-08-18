$(document).ready( function(){

strip = function(s) { return s.replace(/^\s+/, '').replace(/\s+$/, ''); }
remove_punctuation = function(s) { return s.replace(/[,.;]/g,''); }

$('#ptitle').change(function fillURL(){
    if(! $('#pid').attr('readonly')){
        url = strip(this.value).toLowerCase().replace(/\s+/g, '-');
        url = remove_punctuation(url);
        $('#pid').val(url);
        $('#pid').change(); //is this required?
    }    
    return;
});

$('#pid').change( function checkID(){
    $.post('/c/checkID', {pid: strip(this.value)},
         function(available){
            if (available == 'False'){
                msg = 'ID already exists, Choose a different one';
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
