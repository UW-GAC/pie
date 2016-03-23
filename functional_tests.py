"""Test the admin interface."""

from selenium import webdriver, WebDriver
from selenium.webdriver.common.keys import Keys

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import admin

class AdminTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_admin_site(self):
        # User opens web browser and navigates to admin page.
        self.browser.get(self.live_server_url + '/admin/')
        body = self.browser.find_element_by_tag_name('body')
        self.assertIn('Administration', body.text)
        
# class SeleniumInteractionTests(StaticLiveServerTestCase):
#     """Tests that include interaction from a user."""
#     
#     @classmethod
#     def setUpClass(cls):
#         super(SeleniumTests, cls).setUpClass()
#         cls.selenium = WebDriver()
#         
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super(SeleniumTests, cls).tearDownClass()
#     
#     def test_source_all():
#         
#         # Open the source_all page.
#         
#         
#         # Click on the Help button.
#         
#         
#         # Sort by phenotype name.
#         
#         
#         # Sort by study name.
#         
#         
#         # Click on a dbGaP study link
#         
#         
#         # Click on a dbGaP variable link
#         pass