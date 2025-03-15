from moments.models import User
from moments.settings import Operations
from moments.utils import generate_token
from tests import BaseTestCase


class AuthTestCase(BaseTestCase):
    def test_login_normal_user(self):
        response = self.login()
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)

    def test_login_locked_user(self):
        self.login(email='locked@helloflask.com', password='123')
        response = self.client.get('/user/locked')
        data = response.get_data(as_text=True)
        self.assertIn('Your account is locked.', data)

    def test_login_blocked_user(self):
        response = self.login(email='blocked@helloflask.com', password='123')
        data = response.get_data(as_text=True)
        self.assertIn('Your account is blocked.', data)

    def test_fail_login(self):
        response = self.login(email='wrong-username@helloflask.com', password='wrong-password')
        data = response.get_data(as_text=True)
        self.assertIn('Invalid email or password.', data)

    def test_logout_user(self):
        self.login()
        response = self.logout()
        data = response.get_data(as_text=True)
        self.assertIn('Logout success.', data)

    def test_login_protect(self):
        response = self.client.get('/upload', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Please log in to access this page.', data)

    def test_unconfirmed_user_permission(self):
        self.login(email='unconfirmed@helloflask.com', password='123')
        response = self.client.get('/upload', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Please confirm your account first.', data)

    def test_locked_user_permission(self):
        self.login(email='locked@helloflask.com', password='123')
        response = self.client.get('/upload', follow_redirects=True)
        self.assertEqual(response.status_code, 403)

    def test_register_account(self):
        response = self.client.post(
            '/auth/register',
            data=dict(
                name='Grey Li', email='test@helloflask.com', username='test', password='12345678', password2='12345678'
            ),
            follow_redirects=True,
        )
        data = response.get_data(as_text=True)
        self.assertIn('Confirmation email sent, please check your inbox.', data)

    def test_confirm_account(self):
        user = User.query.filter_by(email='unconfirmed@helloflask.com').first()
        self.assertFalse(user.confirmed)
        token = generate_token(user=user, operation=Operations.CONFIRM)
        self.login(email='unconfirmed@helloflask.com', password='123')
        response = self.client.get(f'/auth/confirm/{token}', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Account confirmed.', data)
        self.assertTrue(user.confirmed)

    def test_bad_confirm_token(self):
        self.login(email='unconfirmed@helloflask.com', password='123')
        response = self.client.get('/auth/confirm/bad-token', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid or expired token.', data)
        self.assertNotIn('Account confirmed.', data)

    def test_reset_password(self):
        response = self.client.post(
            '/auth/forget-password',
            data=dict(
                email='normal@helloflask.com',
            ),
            follow_redirects=True,
        )
        data = response.get_data(as_text=True)
        self.assertIn('Password reset email sent, please check your inbox.', data)
        user = User.query.filter_by(email='normal@helloflask.com').first()
        self.assertTrue(user.validate_password('123'))

        token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
        response = self.client.post(
            f'/auth/reset-password/{token}',
            data=dict(email='normal@helloflask.com', password='new-password', password2='new-password'),
            follow_redirects=True,
        )
        data = response.get_data(as_text=True)
        self.assertIn('Password updated.', data)
        self.assertTrue(user.validate_password('new-password'))
        self.assertFalse(user.validate_password('123'))

        # bad token
        response = self.client.post(
            '/auth/reset-password/bad-token',
            data=dict(email='normal@helloflask.com', password='new-password', password2='new-password'),
            follow_redirects=True,
        )
        data = response.get_data(as_text=True)
        self.assertIn('Invalid or expired link.', data)
        self.assertNotIn('Password updated.', data)
