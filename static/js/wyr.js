$(document).ready( function(){

var strip = function(s) { return s.replace(/^\s+/, '').replace(/\s+$/, ''); }
    
var zip_check_event = function(){
    zipcode = strip($('#zipcode').val());
    zip4 = strip($('#zip4').val());
    address = strip($('#addr1').val()) + strip($('#addr2').val());
    $.post('/writerep/verifyzip', {zipcode: zipcode, zip4: zip4, address: address},
        function(dists){
            if (dists == '0'){
                msg = 'No matching address found for this address and zip';
                $('#addr1').focus();
                ret = false;
            }
            else if (dists == '2' && !zip4){
                msg = 'Zip is shared between more than 1 district. Please enter zip4';
                $('#zip4').focus();
                ret = false;
            }
            else{
                msg = '' ;
                ret = load_unload_captcha(dists);
            }
            $('#note_zipcode').html('<strong style="color:red">' + msg + '</strong>');
            return ret;
        });
}

var zip_changed = false
$('#zipcode').change(function(){ 
    zip_changed = true; 
    $('#zip4').focus();
});
$('#zip4').change(function(){ zip_changed = true; });
$('#zip4').blur(function(){
     if (zip_changed){
        zip_check_event();
    }
});

function load_unload_captcha(dist){
    $.get('/writerep/getcaptcha', {dist: dist},
        function (captcha_elmt){ 
            if (captcha_elmt != 'None'){
                $('tr:last').after(captcha_elmt);
                return false;
            }
            else{
                 $('tr td input#captcha').parent().parent().remove()
            }
        });
}

}); //end of document ready