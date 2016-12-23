# pylint: disable=missing-docstring
import arrow

from auth_proxy.application import app


@app.template_filter('shift')
def shift_filter(date, **kwargs):
    return arrow.get(date).shift(**kwargs)


@app.template_filter('format')
def format_filter(date, fmt):
    return arrow.get(date).format(fmt)
