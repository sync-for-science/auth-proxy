# pylint: disable=missing-docstring
from auth_proxy import main


if __name__ == '__main__':
    app = main()

    ordbok = app.extensions['ordbok']
    ordbok.app_run(app, host='0.0.0.0')
