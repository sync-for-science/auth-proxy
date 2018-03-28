import os
from auth_proxy.application import create_app
import unittest
import tempfile
import json


class AuthproxyTestCase(unittest.TestCase):

    def setUp(self):
        self.auth_app = create_app()
        self.db_fd, self.auth_app.config['DATABASE'] = tempfile.mkstemp()
        self.auth_app.testing = True
        self.app = self.auth_app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.auth_app.config['DATABASE'])

    def test_debug_token(self):

        client_id = "test1234"
        expires = 360
        security_labels = "patient,allergies"
        user = "daniel-adams"
        patient_id = "smart-1288992"

        test_token_input = {"client_id": client_id,
                            "expires": expires,
                            "security_labels": security_labels,
                            "user": user,
                            "patient_id": patient_id}

        debug_token = self.app.post('/oauth/debug/token',
                                    data=json.dumps(test_token_input),
                                    content_type='application/json')
        
        assert json.loads(debug_token.get_data(as_text=True))["access_token"]


if __name__ == '__main__':
    unittest.main()