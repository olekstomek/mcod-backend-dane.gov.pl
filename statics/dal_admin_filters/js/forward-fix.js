window.addEventListener('load', function() {
    var $ = (typeof django !== 'undefined' ? django.jQuery : window.jQuery);
    if ($) {
        $('#changelist-filter').children().wrapAll('<form></form>');
    }
});
