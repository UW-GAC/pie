"""Test data migrations in the core app."""

from django.apps import apps
from django.test import TestCase


class SiteTest(TestCase):

    def test_correct_site_name(self):
        """The site has the appropriate name."""
        Site = apps.get_model('sites', 'Site')
        site = Site.objects.get(pk=1)
        self.assertEqual(site.name, 'TOPMed PIE')

    def test_correct_site_domain(self):
        """The site has the appropriate name."""
        Site = apps.get_model('sites', 'Site')
        site = Site.objects.get(pk=1)
        self.assertEqual(site.domain, 'topmedphenotypes.org')


# To get the current expected group permissions from the shell:
# for g in Group.objects.all():
#     print('# --------' + g.name)
#     for p in g.permissions.all():
#         print("('{}', '{}', '{}'),".format(
#             p.content_type.app_label,
#             p.content_type.model,
#             p.codename.split('_')[0]))
class GroupMigrationTest(TestCase):

    def setUp(self):
        super(GroupMigrationTest, self).setUp()
        self.Group = apps.get_model('auth', 'Group')
        self.Permission = apps.get_model('auth', 'Permission')
        self.expected_group_permissions = {
            'dcc_analysts': (
                ('profiles', 'profile', 'change'),
                ('recipes', 'harmonizationrecipe', 'add'),
                ('recipes', 'harmonizationrecipe', 'change'),
                ('recipes', 'harmonizationrecipe', 'delete'),
                ('recipes', 'unitrecipe', 'add'),
                ('recipes', 'unitrecipe', 'change'),
                ('recipes', 'unitrecipe', 'delete'),
                ('tags', 'tag', 'add'),
                ('tags', 'tag', 'change'),
                ('tags', 'tag', 'delete'),
                ('tags', 'taggedtrait', 'add'),
                ('tags', 'taggedtrait', 'change'),
                ('tags', 'taggedtrait', 'delete'),
            ),
            'dcc_developers': (
                ('flatpages', 'flatpage', 'add'),
                ('flatpages', 'flatpage', 'change'),
                ('flatpages', 'flatpage', 'delete'),
                ('profiles', 'profile', 'add'),
                ('profiles', 'profile', 'change'),
                ('profiles', 'profile', 'delete'),
                ('profiles', 'savedsearchmeta', 'add'),
                ('profiles', 'savedsearchmeta', 'change'),
                ('profiles', 'savedsearchmeta', 'delete'),
                ('profiles', 'search', 'add'),
                ('profiles', 'search', 'change'),
                ('profiles', 'search', 'delete'),
                ('recipes', 'harmonizationrecipe', 'add'),
                ('recipes', 'harmonizationrecipe', 'change'),
                ('recipes', 'harmonizationrecipe', 'delete'),
                ('recipes', 'unitrecipe', 'add'),
                ('recipes', 'unitrecipe', 'change'),
                ('recipes', 'unitrecipe', 'delete'),
                ('sessions', 'session', 'add'),
                ('sessions', 'session', 'change'),
                ('sessions', 'session', 'delete'),
                ('tags', 'tag', 'add'),
                ('tags', 'tag', 'change'),
                ('tags', 'tag', 'delete'),
                ('tags', 'taggedtrait', 'add'),
                ('tags', 'taggedtrait', 'change'),
                ('tags', 'taggedtrait', 'delete'),
            ),
            'phenotype_taggers': (
                ('tags', 'taggedtrait', 'add'),
                ('tags', 'taggedtrait', 'change'),
                ('tags', 'taggedtrait', 'delete'),
            ),
            'recipe_submitters': (
                ('recipes', 'harmonizationrecipe', 'add'),
                ('recipes', 'harmonizationrecipe', 'change'),
                ('recipes', 'harmonizationrecipe', 'delete'),
                ('recipes', 'unitrecipe', 'add'),
                ('recipes', 'unitrecipe', 'change'),
                ('recipes', 'unitrecipe', 'delete'),
            ),
        }

    def test_group_existence(self):
        """Expected groups exist."""
        for name in self.expected_group_permissions:
            group = self.Group.objects.get(name=name)
            self.assertIsInstance(group, self.Group)

    def test_no_unexpected_groups(self):
        """No unexpected groups exist."""
        self.assertEqual(self.Group.objects.exclude(name__in=self.expected_group_permissions.keys()).count(), 0)

    def test_analyst_permissions(self):
        """DCC analysts have correct permissions."""
        for name in self.expected_group_permissions:
            group = self.Group.objects.get(name=name)
            for perm_description in self.expected_group_permissions[name]:
                perm = self.Permission.objects.get(content_type__app_label=perm_description[0],
                                                   content_type__model=perm_description[1],
                                                   codename__startswith=perm_description[2])
                self.assertIsInstance(perm, self.Permission)
