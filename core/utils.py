""" """


from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class ViewsAutoLoginTestCase(TestCase):

    # since all views require login, this needs to be run before each test
    # make a class that we can extend for the other test cases
    def setUp(self):
        super(ViewsAutoLoginTestCase, self).setUp()

        self.client = Client()
        self.user = User.objects.create_user('unit@test.com', 'passwd')
        self.client.login(email='unit@test.com', password='passwd')