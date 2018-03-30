from auth_proxy.application import app, create_app
from auth_proxy.models.oauth import Client
from auth_proxy.models.user import User
from auth_proxy.extensions import db
import unittest
import json


class AuthproxyTestCase(unittest.TestCase):

    CLIENT_ID = "test1234"
    CLIENT_SECRET = "secret1234"

    USERNAME = "daniel-adams"
    PASSWORD = "demo-password"

    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.auth_app = create_app()

        with self.auth_app.app_context():
            db.create_all()
            new_client = Client(client_id=self.CLIENT_ID,
                                client_secret=self.CLIENT_SECRET,
                                name=self.CLIENT_ID)

            db.session.add(new_client)

            new_user = User(username=self.USERNAME,
                            password=self.PASSWORD)

            db.session.add(new_user)

            db.session.commit()

        self.auth_app.testing = True
        self.app = self.auth_app.test_client()

    def test_debug_token(self):

        # Create Token
        expires = 360
        scopes = "patient/*.read launch/patient offline_access"
        patient_id = "smart-1288992"

        test_token_input = {"client_id": self.CLIENT_ID,
                            "expires": expires,
                            "scopes": scopes,
                            "user": self.USERNAME,
                            "patient_id": patient_id}

        debug_token_return = self.app.post('/oauth/debug/token',
                                           data=json.dumps(test_token_input),
                                           content_type='application/json')

        # Did we receive the token succesfully?
        access_token = json.loads(debug_token_return.get_data(as_text=True))["access_token"]
        assert access_token

        # Attempt to verify Token
        token_introspection_response = self.app.get('/oauth/debug/introspect?access_token=%s' % access_token)

        # Did we receive the same token we sent?
        returned_access_token = json.loads(token_introspection_response.get_data(as_text=True))["access_token"]
        assert access_token == returned_access_token

if __name__ == '__main__':
    unittest.main()
