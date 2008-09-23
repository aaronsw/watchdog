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
                if (! $('#captcha')[0]){
                    load_captcha(dists);
                }
                ret = true;
            }
            $('#note_zipcode').html('<strong style="color:red">' + msg + '</strong>');
            return ret;
        });
}

$('#zip4').change(zip_check_event);
$('#zip4').blur(zip_check_event);

function load_captcha(dist){
    $.get('/writerep/getcaptcha', {dist: dist},
        function (captcha_elmt){ 
            if (captcha_elmt != 'None'){
                $('tr:last').after(captcha_elmt);
            }
        });
}

}); //end of document ready