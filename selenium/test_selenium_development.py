"""Test the admin interface."""

import time
from os import environ
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.test import Client
from django.contrib.auth.models import User

from trait_browser.factories import StudyFactory, SourceTraitFactory, SourceEncodedValueFactory

# Default operation timeout in seconds.
TIMEOUT = 10
 
# Default operation retry frequency.
POLL_FREQUENCY = 0.5
 
class Wait(WebDriverWait):
    """Custon Wait class for more exception handling and specific timeout & poll frequency.
    
    Reference:
    Jeremy Bowman
    https://www.safaribooksonline.com/blog/2012/11/23/writing-a-selenium-test-framework-for-a-django-site-part-3/
    
    This subclass of Selenium's WebDriverWait has a preset timeout and poll
    frequency. It also deals with a wider variety of exceptions.
    
    This custom Wait class seems like a good idea because of this comment from
    the Django documentation:
    'The tricky thing here is that there's really no such thing as a page load,
    especially in modern Web apps that generate HTML dynamically after the
    server generates the initial document. So, simply checking for the presence
    of <body> in the response might not necessarily be appropriate for all use
    cases.'
    (https://docs.djangoproject.com/en/1.8/topics/testing/tools/#liveservertestcase)
    
    So, I'm following the advice from the O'Reilly blog post to implement this
    custom Wait subclass, which I will use for some other things.
    """
    def __init__(self, driver):
        """ Constructor """
        super(Wait, self).__init__(driver, TIMEOUT, POLL_FREQUENCY)
 
    def until(self, method, message=''):
        """Calls the method provided with the driver as an argument until the
        return value is not False."""
        end_time = time.time() + self._timeout
        while(True):
            try:
                value = method(self._driver)
                if value:
                    return value
            except NoSuchElementException:
                pass
            except StaleElementReferenceException:
                pass
            time.sleep(self._poll)
            if(time.time() > end_time):
                break
        raise TimeoutException(message)
 
    def until_not(self, method, message=''):
        """Calls the method provided with the driver as an argument until the
        return value is False."""
        end_time = time.time() + self._timeout
        while(True):
            try:
                value = method(self._driver)
                if not value:
                    return value
            except NoSuchElementException:
                return True
            except StaleElementReferenceException:
                pass
            time.sleep(self._poll)
            if(time.time() > end_time):
                break
        raise TimeoutException(message)


class SeleniumTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumTestCase, cls).setUpClass()
        cls.selenium = webdriver.Firefox()
        # Use Safari browser.
        # environ["SELENIUM_SERVER_JAR"] = "selenium-server-standalone-2.53.0.jar"
        # cls.selenium = webdriver.Safari(quiet=True)
        # Use Chrome browser.
        # cls.selenium = webdriver.Chrome(executable_path='./chromedriver')

        # Add a superuser to the db.
        cls.client = Client()
        cls.user_password = 'atomicnumber34'
        cls.user = User.objects.create_superuser(username='selenium', email='foo@bar.com', password=cls.user_password)
        
        # Fill the test db with fake data.
        studies = StudyFactory.create_batch(5) # Make 5 studies.
        for study in studies:
            # Make 40 source traits for each study, 10 each with 4 encoded values.
            SourceTraitFactory.create_batch(30, study=study)
            enc_val_traits = SourceTraitFactory.create_batch(10, study=study)
            for trait in enc_val_traits:
                SourceEncodedValueFactory.create_batch(4, source_trait=trait)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTestCase, cls).tearDownClass()
        
    def get_reverse(self, view_name):
        """Use selenium to get the URL for the given reversed view_name URL."""
        self.selenium.get(self.live_server_url + reverse(view_name))
    
    def wait_for_element_by_name(self, name):
        """Wait for a named element to show up on the page."""
        element_is_present = lambda driver: driver.find_element_by_name(name)
        msg = 'An element named {} should be on the page'.format(name)
        element = Wait(self.selenium).until(element_is_present, msg)
    
    def wait_until_visible(self, selector):
        """Wait until the element matching the selector is visible."""
        element_is_visible = lambda driver: self.selenium.find_element_by_css_selector(selector).is_displayed()
        msg = 'The element matching {} should be visible'.format(selector)
        Wait(self.selenium).until(element_is_visible, msg)
        return element
    
    def enter_text(self, name, value):
        """Enter text into a specific element on the page, with improved Wait class."""
        field = self.wait_for_element_by_name(name)
        field.send_keys(value)
        return field
    
    def click(self, selector):
        """Click on a specific element of the page, with improved Wait class."""
        element = self.wait_until_visible(selector)
        element.click()
        return element
        

class HomeTest(SeleniumTestCase):
    
    def test_home(self):
        # Go to the home page.
        self.get_reverse('home')
        # Are the three main page icons there?
        main_elements = self.selenium.find_elements_by_class_name('col-md-4')
        self.assertEqual(3, len(main_elements))
        # Is the navbar there?
        navbar = self.selenium.find_element_by_class_name('navbar')
        self.assertIsNotNone(navbar)
        # Click on the Source phenotypes dropdown menu.
        self.selenium.find_element_by_link_text('Source phenotypes').click()
        time.sleep(1)
        
        self.selenium.find_element_by_link_text('View all').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")

        self.selenium.find_element_by_link_text('Source phenotypes').click()
        self.selenium.find_element_by_link_text('Browse by study').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")

        self.selenium.find_element_by_link_text('Source phenotypes').click()
        self.selenium.find_element_by_link_text('Search').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")


class AdminTest(SeleniumTestCase):

    def test_admin(self):
        # Open web browser and navigate to admin page.
        self.get_reverse('admin:index')
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('Administration', body.text)
        # Log in to the admin interface.
        username = self.selenium.find_element_by_id("id_username")
        password = self.selenium.find_element_by_id("id_password")
        username.send_keys(self.user.username)
        password.send_keys(self.user_password)
        self.selenium.find_element_by_class_name('submit-row').click()       
        time.sleep(1)
        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_link_text('Source encoded values').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")

        self.selenium.find_element_by_link_text('Source traits').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")
        
        self.selenium.find_element_by_link_text('Studies').click()
        time.sleep(1)
        self.selenium.execute_script("window.history.go(-1)")        