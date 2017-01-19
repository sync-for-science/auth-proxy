$(function () {
    var $next = $('#confirmation-item .btn:contains("Next")');
    var $boxes = $('#confirmation-item [rel="confirm"]');
    var $all = $boxes.add($next);

    $boxes.on('change', function (event) {
        var $el = $(event.currentTarget);
        var index = $all.index($el) + 1 + Number($el.is(':checked'));
        var $after = $all.slice(index);

        $all.attr('disabled', false);
        $after.attr('disabled', true)
            .attr('checked', false);
    });
    $boxes.first().trigger('change');

    $('[data-toggle="popover"]').popover();
    $('[data-slide]').on('click', function() {
        $('[data-toggle="popover"]').popover('hide');
    });

    $('time[data-format]').each(function (ix, el) {
        var $el = $(el);
        var dt = moment($el.attr('datetime'));

        $el.text(dt.format($el.data('format')));
    });

    $('[rel="change"]').on('click', function (event) {
        var $el = $(event.currentTarget);
        var $group = $el.closest('.form-group');
        var $target = $group.find('> :nth-child(2) input')
            .not('[value="patient"]');

        $el.hide();
        $target.attr('disabled', false);

        if ($target.length === 1) {
            $target.focus();
        }
    });

    $('[data-toggle="print"]').on('click', function (event) {
        window.print();
    });

    $('#confirm-expires').on('change', function (event) {
        var $el = $(event.currentTarget);
        var $target = $('#approve-expires');
        var dt = moment($el.val());
        var $submit = $('[name="expires"]');

        $target.text(dt.format($target.data('format')));
        $submit.val($el.val());
    });
    $('#confirm-expires').on('blur', function (event) {
        var $el = $(event.currentTarget);
        var dt = moment($el.val());

        if (dt > moment($el.attr('max'))) {
            dt = moment($el.attr('max'));
        }

        if (dt < moment($el.attr('min'))) {
            dt = moment($el.attr('min'));
        }

        $el.val(dt.format('YYYY-MM-DD')).trigger('change');
    });

    $('#confirm-security-labels').on('change', ':checkbox', function (event) {
        var $approve = $('#approve-security-labels').html('');
        var $submit = $('[name="security_labels"]');
        var $inputs = $('#confirm-security-labels :checkbox');
        var inputs = [];

        $inputs.each(function (ix, el) {
            var $el = $(el);
            var val = $el.val();

            if (val === 'vital-signs') {
                val = 'vital signs';
            }

            if ($el.is(':checked')) {
                inputs.push(val);
                $approve.append('<li>' + val + '</li>');
            } else {
                $approve.append('<li><del class="text-muted">' + val + '</del></li>');
            }
        });
        $submit.val(inputs.join(' '));
    });
});
