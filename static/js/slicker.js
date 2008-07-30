$(document).ready(function() {
 // hides the slickbox as soon as the DOM is ready (a little sooner that page load)
  $('#login').hide();
  $('#feedback').hide();
  $('#footer-feedback').show();
  $('#footer-login').hide();
  
 // shows and hides and toggles the slickbox on click  
  $('#slick-show').click(function() {
    $('#slickbox').show('slow');
    return false;
  });
  $('#slick-hide').click(function() {
    $('#slickbox').hide('fast');
    return false;
  });


  $('#login-toggle').click(function() {
    $('#login').toggle(400);
    return false;
  });
  $('#feedback-toggle').click(function() {
    $('#feedback').toggle(400);
    $('#footer-login').toggle(400);
    return false;
  });
  $('#footer-feedback-toggle').click(function() {
    $('#footer-feedback').toggle(400);
    return false;
  });
  $('#footer-login-toggle').click(function() {
    $('#footer-login').toggle(400);
    return false;
  });




 // slides down, up, and toggle the slickbox on click    
  $('#slick-down').click(function() {
    $('#slickbox').slideDown('slow');
    return false;
  });
  $('#slick-up').click(function() {
    $('#slickbox').slideUp('fast');
    return false;
  });
  $('#slick-slidetoggle').click(function() {
    $('#slickbox').slideToggle(400);
    return false;
  });
});




function toggleVisibility(id, NNtype, IEtype, WC3type) {
    if (document.getElementById) {
        eval("document.getElementById(id).style.visibility = \"" + WC3type + "\"");
    } else {
        if (document.layers) {
            document.layers[id].visibility = NNtype;
        } else {
            if (document.all) {
                eval("document.all." + id + ".style.visibility = \"" + IEtype + "\"");
            }
        }
    }
}

function ChangeZ(id) {
obj = document.getElementById("existingLayerID");
if (typeof obj!="undefined")
{
 obj.style.zIndex=50;
}
}

function tOn(id) {
   toggleVisibility(id, "show", "visible", "visible") ;
   }
function tOff(id) {
   toggleVisibility(id, 'hidden', 'hidden', 'hidden') ;
   }

