"""Automated testing of the entire site interactively."""

import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from core.build_test_db import build_test_db
import tags.factories
import tags.models
import trait_browser.models
import trait_browser.factories
import trait_browser.views

User = get_user_model()


class SeleniumTestCase(StaticLiveServerTestCase):
    # Note that LiveServerTestCase inherits from TransactionTestCase, so each test method runs inside a databse
    # transaction. This makes setUpClass and setUpTestData classmethods useless.

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

    def login_superuser(self):
        self.get_reverse('login')
        self.superuser_password = 'atomicnumber34'
        self.superuser = User.objects.create_superuser(email='selenium@test.com', password=self.superuser_password)
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')
        username.send_keys(self.superuser.email)
        password.send_keys(self.superuser_password)
        self.selenium.find_element_by_xpath("//button[@type='submit']").click()

    def login_user(self):
        self.get_reverse('login')
        self.user_password = 'atomicnumber16'
        self.user = User.objects.create_user(email='sulfur@test.com', password=self.user_password)
        username = self.selenium.find_element_by_id('id_username')
        password = self.selenium.find_element_by_id('id_password')
        username.send_keys(self.user.email)
        password.send_keys(self.user_password)
        self.selenium.find_element_by_xpath("//button[@type='submit']").click()


class UserAutoLoginSeleniumTestCase(SeleniumTestCase):

    def setUp(self):
        super(UserAutoLoginSeleniumTestCase, self).setUp()
        self.login_user()
        time.sleep(1)


class SuperuserAutoLoginSeleniumTestCase(SeleniumTestCase):

    def setUp(self):
        super(SuperuserAutoLoginSeleniumTestCase, self).setUp()
        self.login_superuser()
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

        self.selenium.find_element_by_link_text('Study phenotypes').click()
        self.selenium.find_element_by_link_text('Search variables').click()
        time.sleep(1)

        self.selenium.find_element_by_link_text('Study phenotypes').click()
        self.selenium.find_element_by_link_text('Studies').click()
        time.sleep(1)

        self.selenium.find_element_by_link_text('Study phenotypes').click()
        self.selenium.find_element_by_link_text('Datasets').click()
        time.sleep(1)

        self.selenium.find_element_by_link_text('Study phenotypes').click()
        self.selenium.find_element_by_link_text('Variables').click()
        time.sleep(1)


class AdminTestCase(SuperuserAutoLoginSeleniumTestCase):

    def setUp(self):
        super(AdminTestCase, self).setUp()
        # Open web browser and navigate to admin page.
        self.get_reverse('admin:index')
        time.sleep(1)

    def test_admin_landing_page(self):
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('administration', body.text)

    def test_trait_browser_admin(self):
        self.selenium.find_element_by_xpath("//a[@title='Models in the Trait_Browser application']").click()
        time.sleep(1)

        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_link_text('Allowed update reasons').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Global studies').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonization units').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized trait encoded values').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized trait sets').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonized trait set versions').click()
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

    def test_recipes_admin(self):
        self.selenium.find_element_by_xpath("//a[@title='Models in the Recipes application']").click()
        time.sleep(1)

        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_link_text('Harmonization unit recipes').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Harmonization recipes').click()

    def test_tags_admin(self):
        self.selenium.find_element_by_xpath("//a[@title='Models in the Tags application']").click()
        time.sleep(1)

        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_link_text('Phenotype tags').click()
        time.sleep(1)
        self.go_back()

        self.selenium.find_element_by_link_text('Tagged phenotypes').click()

    def test_profiles_admin(self):
        # Navigate to each of the admin model interfaces in turn.
        self.selenium.find_element_by_xpath("//a[@title='Models in the Profiles application']").click()
        time.sleep(1)

        self.selenium.find_element_by_link_text('Profiles').click()


class SourceTraitSearchTestCase(UserAutoLoginSeleniumTestCase):

    def setUp(self):
        super(SourceTraitSearchTestCase, self).setUp()
        build_test_db()
        # Open the Search page.
        self.get_reverse('trait_browser:source:traits:search')
        time.sleep(1)

    def run_search(self, variable_name=None, match_whole_name=None, variable_description=None, dataset_name=None,
                   dataset_description=None, study_list=None):
        """Submit a search for the given search string."""
        # Find all of the search form fields.
        variable_name_field = self.selenium.find_element_by_id('id_name')
        match_whole_name_checkbox = self.selenium.find_element_by_id('id_match_exact_name')
        variable_description_field = self.selenium.find_element_by_id('id_description')
        dataset_name_field = self.selenium.find_element_by_id('id_dataset_name')
        dataset_description_field = self.selenium.find_element_by_id('id_dataset_description')
        study_field = self.selenium.find_element_by_id('id_studies')
        # Type input into the form fields.
        # TODO: Implement all of the new search fields.
        variable_name_field.send_keys(variable_name)
        # Submit the form.
        self.selenium.find_element_by_id('submit-id-submit').click()
        time.sleep(1)

    def test_source_trait_search_all_studies_good_text(self):
        """Test the SourceTrait search page with a string you know is in one of the SourceTraits in the test db."""
        # Get the trait name for the first trait you can find.
        good_text = trait_browser.models.SourceTrait.objects.all()[0].i_trait_name
        self.run_search(variable_name=good_text)
        result_count = len(trait_browser.searches.search_source_traits(name=good_text))
        self.check_table_view(expected_rows=result_count)

    # def test_source_trait_search_all_studies_bad_text(self):
    #     """Test the SourceTrait search page with a string is not in any of the traits in the test db."""
    #     bad_text = 'very_unlikely_search_string'
    #     self.run_search(name=bad_text)
    #     self.check_table_view()
    #     # TODO: proper handling when there are 0 expected rows. Currently, the row count
    #     # is 1 when it should be 0 because "no results" is in a row of the table.
    #     # This will likely need to change anyway because of changes to searching later on.
    # 
    # def test_source_trait_search_single_study_good_text(self):
    #     """Test the SourceTrait search page with a trait name that is in a given study, within the given study."""
    #     study = trait_browser.models.Study.objects.all()[0]
    #     study_trait = trait_browser.models.SourceTrait.objects.filter(
    #         source_dataset__source_study_version__study=study)[0]
    #     good_text = study_trait.i_trait_name
    #     self.run_search(name=good_text, study_list=[study])
    #     # This will find many more results than you expect, because the list of words
    #     # that Faker uses is fairly small. The result is that a given fake trait name
    #     # will likely end up in the trait descriptions of many other traits.
    # 
    # def test_source_trait_search_single_study_good_description_text(self):
    #     """Search page finds a trait based on description, within a given study."""
    #     # This search string is more specific, so should only find one result
    #     study = trait_browser.models.Study.objects.all()[0]
    #     study_trait = trait_browser.models.SourceTrait.objects.filter(
    #         source_dataset__source_study_version__study=study)[0]
    #     good_text = study_trait.i_description
    #     self.run_search(description=good_text, study_list=[study])
    # 
    # def test_source_trait_search_specific_text_wrong_study(self):
    #     """Test the SourceTrait search page by searching for a long search phrase in the wrong study."""
    #     # This search string is more specific, so should only find one result
    #     studies = trait_browser.models.Study.objects.all()
    #     study = studies[0]
    #     study_trait = trait_browser.models.SourceTrait.objects.filter(
    #         source_dataset__source_study_version__study=study)[0]
    #     good_text = study_trait.i_description
    #     self.run_search(description=good_text, study_list=[studies[1]])


class TablePageTestCase(UserAutoLoginSeleniumTestCase):

    def setUp(self):
        super(TablePageTestCase, self).setUp()
        build_test_db()

    def test_source_all_table(self):
        """Run check_table_view on the All source traits table page. Check the link for a source trait detail page."""
        total_source_traits = trait_browser.models.SourceTrait.objects.count()
        self.get_reverse('trait_browser:source:traits:list')
        self.check_table_view(expected_rows=total_source_traits)
        # Check the detail page for the first listed SourceTrait.
        detail_link = self.selenium.find_element_by_class_name('i_trait_name')
        detail_link.click()
        self.go_back()

    def test_source_study_list_table(self):
        """Run check_table_view on the Browse by study table page. Follow the link for one study."""
        study_count = trait_browser.models.Study.objects.count()
        self.get_reverse('trait_browser:source:studies:list')
        self.check_table_view(expected_rows=study_count)
        # Check the page for the first listed Study.
        study_name = trait_browser.models.Study.objects.all().order_by('i_study_name')[0].i_study_name
        study_link = self.selenium.find_element_by_link_text(study_name)
        study_link.click()

    def test_source_study_detail_table(self):
        """Study detail page works."""
        study = trait_browser.models.Study.objects.all()[0]
        trait_count = trait_browser.models.SourceTrait.objects.filter(
            source_dataset__source_study_version__study=study).all().count()
        self.get_reverse('trait_browser:source:studies:pk:traits:list', study.pk)
        self.check_table_view(expected_rows=trait_count)


class TagViewsTestCase(UserAutoLoginSeleniumTestCase):

    def setUp(self):
        super().setUp()
        self.login_superuser()
        self.study_version = trait_browser.factories.SourceStudyVersionFactory.create()
        self.tag = tags.factories.TagFactory.create()
        self.tagged_traits = tags.factories.TaggedTraitFactory.create_batch(
            2, trait__source_dataset__source_study_version=self.study_version, tag=self.tag)

    def test_dcc_review_loop_skip(self):
        """Skip button works as expected for DCC Review loop."""
        self.get_reverse('tags:tag:study:begin-dcc-review', self.tag.pk, self.study_version.study.pk)
        message = self.selenium.find_element_by_class_name('alert')
        self.assertIn('2 tagged variables left', message.text)  # Expected alert
        title = self.selenium.find_element_by_tag_name('h2')
        self.assertIn(self.tagged_traits[0].__str__(), title.text)  # Expected title text
        skip_button = self.selenium.find_element_by_id('submit-id-skip')
        time.sleep(1)
        skip_button.click()
        time.sleep(2)
        message = self.selenium.find_element_by_class_name('alert')
        self.assertIn('1 tagged variable left', message.text)  # Alert changes
        title = self.selenium.find_element_by_tag_name('h2')
        self.assertIn(self.tagged_traits[1].__str__(), title.text)  # Title changes
        skip_button = self.selenium.find_element_by_id('submit-id-skip')
        time.sleep(1)
        skip_button.click()
        time.sleep(2)
        # And you're returned to the tag+study combo page.
        tag_study_table_url = reverse('tags:tag:study:list', args=[self.tag.pk, self.study_version.study.pk])
        self.assertIn(tag_study_table_url, self.selenium.current_url)
        self.assertEqual(tags.models.DCCReview.objects.count(), 0)  # No DCC Reviews were created.

    def test_dcc_decision_loop_skip(self):
        """Skip button works as expected for DCC Decision loop."""
        for tt in self.tagged_traits:
            dcc_review = tags.factories.DCCReviewFactory.create(
                tagged_trait=tt, status=tags.models.DCCReview.STATUS_FOLLOWUP)
            tags.factories.StudyResponseFactory.create(
                dcc_review=dcc_review, status=tags.models.StudyResponse.STATUS_DISAGREE)
        self.get_reverse('tags:tag:study:begin-dcc-decision', self.tag.pk, self.study_version.study.pk)
        message = self.selenium.find_element_by_class_name('alert')
        self.assertIn('2 tagged variables left', message.text)  # Expected alert
        title = self.selenium.find_element_by_tag_name('h2')
        self.assertIn(self.tagged_traits[0].__str__(), title.text)  # Expected title text
        skip_button = self.selenium.find_element_by_id('submit-id-skip')
        time.sleep(1)
        skip_button.click()
        time.sleep(2)
        message = self.selenium.find_element_by_class_name('alert')
        self.assertIn('1 tagged variable left', message.text)  # Alert changes
        title = self.selenium.find_element_by_tag_name('h2')
        self.assertIn(self.tagged_traits[1].__str__(), title.text)  # Title changes
        skip_button = self.selenium.find_element_by_id('submit-id-skip')
        time.sleep(1)
        skip_button.click()
        time.sleep(2)
        # And you're returned to the tag+study combo page.
        tag_study_table_url = reverse('tags:tag:study:list', args=[self.tag.pk, self.study_version.study.pk])
        self.assertIn(tag_study_table_url, self.selenium.current_url)
        self.assertEqual(tags.models.DCCDecision.objects.count(), 0)  # No DCC Decisions were created.
