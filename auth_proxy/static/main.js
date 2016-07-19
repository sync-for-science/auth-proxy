$(function () {
  $('[rel=post]').on('click', function (event) {
    event.preventDefault();

    var $el = $(event.currentTarget),
        $form = $('<form />', {
          action: $el.attr('href'),
          method: 'post'
        });

    $.each($el.data(), function (key, value) {
      $form.append($('<input />', {
        name: key,
        value: value
      }));
    });

    if (confirm('Are you sure?')) {
      $form.submit();
    }
  });
});
