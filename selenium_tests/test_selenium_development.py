"""Automated testing of the entire site interactively."""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re
import time

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse

from core.build_test_db import build_test_db
import trait_browser.models
import trait_browser.factories
import trait_browser.views

User = get_user_model()


class SeleniumTestCase(StaticLiveServerTestCase):

    page_regex = re.compile(r'Page (\d+) of (\d+)')

    @classmethod
    def setUpClass(cls):
        super(SeleniumTestCase, cls).setUpClass()
        # cls.selenium = webdriver.Firefox()
        # Firefox now no longer works natively with the Webdriver. Instead you have to install
        # a driver much like for Safari and Chrome. Look into this further later.

        # Use Safari browser.
        # environ["SELENIUM_SERVER_JAR"] = "selenium_tests/selenium-server-standalone-2.53.0.jar"
        # cls.selenium = webdriver.Safari(quiet=True)

        # Use Chrome browser.
        # Note that the current chromedriver is intended for Macs, and this should probably
        # change to some other system where the chromedriver is not tracked, like the secrets.
        cls.selenium = webdriver.Chrome(executable_path='selenium_tests/chromedriver')

    def setUp(self):
        super(SeleniumTestCase, self).setUp()
        # Add a superuser to the db.
        self.superuser_password = 'atomicnumber34'
        self.superuser = User.objects.create_superuser(email='selenium@test.com', password=self.superuser_password)

        self.user_password = 'atomicnumber16'
        self.user = User.objects.create_user(email='sulfur@test.com', password=self.user_password)
        # Fill the test db with fake data.
        build_test_db(5, (1, 6), (5, 11), (5, 20), (2, 10))

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def get_reverse(self, view_name, *args):
        """Use selenium to get the URL for the given reversed view_name URL."""
        self.selenium.get(self.live_server_url + reverse(view_name, args=args))

    def go_back(self):
        """Use selenium driver to go back one page."""
        self.selenium.execute_script("window.history.go(-1)")

    def check_table_presence(self):
        """Check that a table is present on the page."""
        try:
            table = self.selenium.find_element_by_class_name('table-container')
        except NoSuchElementException:
            table = None
        self.assertIsNotNone(table, msg='There is no table on this page.')

    def click_next_button(self):
        """Click on the first link with text 'Next'."""
        self.selenium.find_element_by_link_text('Next').click()

    def click_previous_button(self):
        """Click on the first link with text 'Previous'."""
        self.selenium.find_element_by_link_text('Previous').click()

    def check_table_view(self, expected_rows=None):
        """Reusable testing function for django-tables2 views.

        Tests functionality of a django-tables2 view page, and checks that it has
        the expected number of rows.

        Args:
            expected_rows: int; the number of rows that should be in the table
            on the page being tested
        """
        # Is there a table?
        self.check_table_presence()

        # Does sorting by columns work?
        sortable_column_names = [el.text for el in self.selenium.find_elements_by_class_name('orderable')]
        for column_name in sortable_column_names:
            link = self.selenium.find_element_by_link_text(column_name)
            link.click()
            self.check_table_presence()
            self.go_back()

        # Count the pages, table rows, and table columns.
        column_count = len(self.selenium.find_elements_by_tag_name('th'))
        # This would include the header row, if not for subtracting 1.
        row_count_page1 = len(self.selenium.find_elements_by_tag_name('tr')) - 1
        # Get the number of pages, if multiple.
        try:    # There are multiple pages.
            page_count_text = self.selenium.find_element_by_class_name('cardinality').text
            page_regex_match = re.search(self.page_regex, page_count_text)
            current_page = page_regex_match.group(1)
            page_count = int(page_regex_match.group(2))
        except NoSuchElementException:    # There is only one page.
            current_page = 1
            page_count = 1

        # Check next and previous buttons, if multiple pages.
        if page_count > 1:
            self.click_next_button()
            self.check_table_presence()
            self.click_previous_button()
            self.check_table_presence()

        # Check that the number of rows is correct.
        if expected_rows is not None:
            # Get the count of rows from all the pages, if you know there are multiple pages.
            if page_count > 1:
                # Add page number specification for the last page to the current URL.
                current_url = self.selenium.current_url
                if '?' in current_url:
                    last_page_url = current_url + '&page={}'.format(page_count)
                else:
                    last_page_url = current_url + '?page={}'.format(page_count)
                # Go to the last page and get the number of rows there.
                self.selenium.get(last_page_url)
                row_count_last_page = len(self.selenium.find_elements_by_tag_name('tr')) - 1
                # Go back to the first page URL.
                self.selenium.get(current_url)
                # Total the rows for all pages.
                previous_page_rows = trait_browser.views.TABLE_PER_PAGE * (page_count - 1)
                total_rows = previous_page_rows + row_count_last_page
            else:
                total_rows = row_count_page1
            # Test the number of expected rows.
            self.assertEqual(expected_rows, total_rows)


class UserAutoLoginSeleniumTestCase(SeleniumTestCase):

    def setUp(self):
        super(UserAutoLoginSeleniumTestCase, self).setUp()
        # login
        self.get_reverse('login')
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')
        username.send_keys(self.user.email)
        password.send_keys(self.user_password)
        self.selenium.find_element_by_id('submit-button').click()
        time.sleep(1)


class HomeTestCase(SeleniumTestCase):

    def test_home(self):
        # Go to the home page.
        self.get_reverse('home')
        # Are the three main page icons there?
        main_elements = self.selenium.find_elements_by_class_name('col-md-4')
        self.assertEqual(2, len(main_elements))
        # Is the navbar there?
        navbar = self.selenium.find_element_by_class_name('navbar')
        self.assertIsNotNone(navbar)
        # Click on the Source phenotypes dropdown menu.
        self.selenium.find_element_by_link_text('Source phenotypes').click()
        time.sleep(1)

        self.selenium.find_element_by_link_text('View all').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source phenotypes').click()
        self.selenium.find_element_by_link_text('Browse by study').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source phenotypes').click()
        self.selenium.find_element_by_link_text('Search').click()
        time.sleep(1)
        self.go_back()


class AdminTestCase(SeleniumTestCase):

    def test_admin(self):
        # Open web browser and navigate to admin page.
        self.get_reverse('admin:index')
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('administration', body.text)
        # Log in to the admin interface.
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')
        username.send_keys(self.superuser.email)
        password.send_keys(self.superuser_password)
        self.selenium.find_element_by_class_name('btn-primary').click()
        time.sleep(1)
        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_link_text('GlobalStudies').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized trait encoded values').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized trait sets').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized traits').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source datasets').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source study versions').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source trait encoded values').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Source traits').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Studies').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Subcohorts').click()
        time.sleep(1)
        self.go_back()


class SourceTraitSearchTestCase(UserAutoLoginSeleniumTestCase):

    def setUp(self):
        super(SourceTraitSearchTestCase, self).setUp()
        # Open the Search page.
        self.get_reverse('trait_browser:source:search')
        time.sleep(1)

    def run_search(self, search_string, study_list=None):
        """Submit a search for the given search string."""
        search_text = self.selenium.find_element_by_id('id_text')
        search_text.send_keys(search_string)
        time.sleep(1)
        if study_list is not None:
            studies_with_ranks = [(study, i + 1) for (i, study,) in
                                  enumerate(trait_browser.models.Study.objects.all().order_by('i_study_name')) if
                                  study in study_list]
            for (study, rank) in studies_with_ranks:
                self.selenium.find_element_by_id('id_study_{}'.format(rank)).click()
            time.sleep(1)
        self.selenium.find_element_by_id('submit-id-submit').click()
        time.sleep(1)

    def test_source_trait_search_all_studies_good_text(self):
        """Test the SourceTrait search page with a string you know is in one of the SourceTraits in the test db."""
        # Get the trait name for the first trait you can find.
        good_text = trait_browser.models.SourceTrait.objects.all()[0].i_trait_name
        self.run_search(good_text)
        result_count = len(trait_browser.views.search(good_text, 'source'))
        self.check_table_view(expected_rows=result_count)

    def test_source_trait_search_all_studies_bad_text(self):
        """Test the SourceTrait search page with a string is not in any of the traits in the test db."""
        bad_text = 'very_unlikely_search_string!'
        self.run_search(bad_text)
        self.check_table_view()
        # TODO: proper handling when there are 0 expected rows. Currently, the row count
        # is 1 when it should be 0 because "no results" is in a row of the table.
        # This will likely need to change anyway because of changes to searching later on.

    def test_source_trait_search_single_study_good_text(self):
        """Test the SourceTrait search page with a trait name that is in a given study, within the given study."""
        study = trait_browser.models.Study.objects.all()[0]
        study_trait = trait_browser.models.SourceTrait.objects.filter(
            source_dataset__source_study_version__study=study)[0]
        good_text = study_trait.i_trait_name
        self.run_search(good_text, [study])
        # This will find many more results than you expect, because the list of words
        # that Faker uses is fairly small. The result is that a given fake trait name
        # will likely end up in the trait descriptions of many other traits.

    def test_source_trait_search_single_study_good_specific_text(self):
        """Search page finds a trait based on description, within a given study."""
        # This search string is more specific, so should only find one result
        study = trait_browser.models.Study.objects.all()[0]
        study_trait = trait_browser.models.SourceTrait.objects.filter(
            source_dataset__source_study_version__study=study)[0]
        good_text = study_trait.i_description
        self.run_search(good_text, [study])

    def test_source_trait_search_specific_text_wrong_study(self):
        """Test the SourceTrait search page by searching for a long search phrase in the wrong study."""
        # This search string is more specific, so should only find one result
        studies = trait_browser.models.Study.objects.all()
        study = studies[0]
        study_trait = trait_browser.models.SourceTrait.objects.filter(
            source_dataset__source_study_version__study=study)[0]
        good_text = study_trait.i_description
        self.run_search(good_text, [studies[1]])


class TablePageTestCase(UserAutoLoginSeleniumTestCase):

    def test_source_all_table(self):
        """Run check_table_view on the All source traits table page. Check the link for a source trait detail page."""
        total_source_traits = trait_browser.models.SourceTrait.objects.count()
        self.get_reverse('trait_browser:source:all')
        # Expect 2 extra rows here because of the table containing the upper right buttons.
        self.check_table_view(expected_rows=total_source_traits + 2)
        # Check the detail page for the first listed SourceTrait.
        detail_link = self.selenium.find_element_by_class_name('i_trait_name')
        detail_link.click()
        self.go_back()

    def test_source_study_list_table(self):
        """Run check_table_view on the Browse by study table page. Follow the link for one study."""
        study_count = trait_browser.models.Study.objects.count()
        self.get_reverse('trait_browser:source:study:list')
        self.check_table_view(expected_rows=study_count)
        # Check the page for the first listed Study.
        study_name = trait_browser.models.Study.objects.all().order_by('i_study_name')[0].i_study_name
        study_link = self.selenium.find_element_by_link_text(study_name)
        study_link.click()
        self.check_table_presence()
        self.go_back()

    def test_source_study_detail_table(self):
        """Run check_table_view on the Study detail list page (from a link in the Browse by study table)."""
        study = trait_browser.models.Study.objects.all()[0]
        trait_count = trait_browser.models.SourceTrait.objects.filter(
            source_dataset__source_study_version__study=study).all().count()
        self.get_reverse('trait_browser:source:study:detail', study.pk)
        # Expect 2 extra rows here because of the table containing the upper right buttons.
        self.check_table_view(expected_rows=trait_count + 2)
