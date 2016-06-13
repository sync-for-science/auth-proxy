# pylint: disable=missing-docstring
from auth_proxy import main


app = main()

if __name__ == '__main__':
    ordbok = app.extensions['ordbok']  # pylint: disable=invalid-name
    ordbok.app_run(app, host='0.0.0.0')
