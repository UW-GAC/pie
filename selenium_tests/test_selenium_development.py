"""Test the admin interface."""

import time
from os import environ
from selenium import webdriver

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.test import Client
from django.contrib.auth.models import User

from trait_browser.factories import StudyFactory, SourceTraitFactory, SourceEncodedValueFactory
from trait_browser.models import Study, SourceTrait, SourceEncodedValue

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
        
    def setUp(self):
        super(SeleniumTestCase, self).setUp()
        # Add a superuser to the db.
        self.user_password = 'atomicnumber34'
        self.user = User.objects.create_superuser(username='selenium', email='foo@bar.com', password=self.user_password)
        
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
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')
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


class SourceTraitSearchTest(SeleniumTestCase):
    
    def setUp(self):
        super(SourceTraitSearchTest, self).setUp()
        # Open the Search page.
        self.get_reverse('trait_browser:source_search')
        
    def run_search(self, search_string, study_list=None):
        """Submit a search for the given search string."""
        search_text = self.selenium.find_element_by_id('id_text')
        search_text.send_keys(search_string)
        time.sleep(1)
        if study_list is not None:
            studies_with_ranks = [(study, i+1) for (i, study,) in enumerate(Study.objects.all().order_by('name')) if study in study_list]
            for (study, rank) in studies_with_ranks:
                self.selenium.find_element_by_id('id_study_{}'.format(rank)).click()
            time.sleep(2)
        self.selenium.find_element_by_id('submit-id-submit').click()
        time.sleep(3)
    
    def test_source_trait_search_all_studies_good_text(self):
        """Test the SourceTrait search page with a string you know is in one of the SourceTraits in the test db."""
        # Get the trait name for the first trait you can find.
        good_text = SourceTrait.objects.all()[0].name
        self.run_search(good_text)
    
    def test_source_trait_search_all_studies_bad_text(self):
        """Test the SourceTrait search page with a string is not in any of the traits in the test db."""
        bad_text = 'very_unlikely_search_string!'
        self.run_search(bad_text)
    
    def test_source_trait_search_single_study_good_text(self):
        """Test the SourceTrait search page with a trait name that is in a given study, searching only within that study."""
        study = Study.objects.all()[0]
        study_trait = study.sourcetrait_set.all()[0]
        good_text = study_trait.name
        self.run_search(good_text, [study])
        # This will find many more results than you expect, because the list of words
        # that Faker uses is fairly small. The result is that a given fake trait name
        # will likely end up in the trait descriptions of many other traits.
        
    def test_source_trait_search_single_study_good_specific_text(self):
        """Test the SourceTrait search page with a long phrase from a trait description that is in a given study, searching only within that study."""
        # This search string is more specific, so should only find one result
        study = Study.objects.all()[0]
        study_trait = study.sourcetrait_set.all()[0]
        good_text = study_trait.description
        self.run_search(good_text, [study])
        
    def test_source_trait_search_specific_text_wrong_study(self):
        """Test the SourceTrait search page by searching for a long search phrase in the wrong study."""
        # This search string is more specific, so should only find one result
        studies = Study.objects.all()
        study = studies[0]
        study_trait = study.sourcetrait_set.all()[0]
        good_text = study_trait.description
        self.run_search(good_text, [studies[1]])
    
        
        
        