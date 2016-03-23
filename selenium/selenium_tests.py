"""Test the admin interface."""

from os import environ
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import admin
from django.core.urlresolvers import reverse

class SeleniumTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumTest, cls).setUpClass()
        cls.selenium = webdriver.Firefox()

        # environ["SELENIUM_SERVER_JAR"] = "selenium-server-standalone-2.53.0.jar"
        # cls.selenium = webdriver.Safari(quiet=True)
        
        # cls.selenium = webdriver.Chrome(executable_path='./chromedriver')

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTest, cls).tearDownClass()


class HomeTest(SeleniumTest):
    
    def test_home(self):
        self.selenium.get(self.live_server_url + reverse('home'))


class AdminTest(SeleniumTest):

    def test_admin(self):
        # User opens web browser and navigates to admin page.
        self.selenium.get(self.live_server_url + reverse('admin:index'))
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('Administration', body.text)