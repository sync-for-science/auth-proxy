# pylint: disable=missing-docstring
from auth_proxy import main


if __name__ == '__main__':
    app = main()
    app.run(host='0.0.0.0')
