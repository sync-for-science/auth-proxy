# pylint: disable=missing-docstring
from auth_proxy import main


if __name__ == '__main__':
    app = main()  # pylint: disable=invalid-name
    app.run(host='0.0.0.0')
