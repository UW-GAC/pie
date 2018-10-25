"""Test data migrations in the core app."""

from django.apps import apps
from django.test import TestCase

from core.factories import UserFactory


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
                ('tags', 'dccreview', 'add'),
                ('tags', 'dccreview', 'change'),
                ('tags', 'dccreview', 'delete'),
                ('tags', 'dccdecision', 'add'),
                ('tags', 'dccdecision', 'change'),
            ),
            'dcc_developers': (
                ('flatpages', 'flatpage', 'add'),
                ('flatpages', 'flatpage', 'change'),
                ('flatpages', 'flatpage', 'delete'),
                ('profiles', 'profile', 'add'),
                ('profiles', 'profile', 'change'),
                ('profiles', 'profile', 'delete'),
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
                ('tags', 'dccreview', 'add'),
                ('tags', 'dccreview', 'change'),
                ('tags', 'dccreview', 'delete'),
                ('tags', 'dccdecision', 'add'),
                ('tags', 'dccdecision', 'change'),
                ('tags', 'dccdecision', 'delete'),
            ),
            'phenotype_taggers': (
                ('tags', 'taggedtrait', 'add'),
                ('tags', 'taggedtrait', 'change'),
                ('tags', 'taggedtrait', 'delete'),
                ('tags', 'studyresponse', 'add'),
                ('tags', 'studyresponse', 'change'),
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

    def test_group_permissions_expected(self):
        """Each group has the expected permissions."""
        # for g in self.Group.objects.all():
        #     print('# --------' + g.name)
        #     for p in g.permissions.all():
        #         print("('{}', '{}', '{}'),".format(
        #             p.content_type.app_label,
        #             p.content_type.model,
        #             p.codename.split('_')[0]))
        missing_permission_msgs = []
        for group_name in self.expected_group_permissions:
            group = self.Group.objects.get(name=group_name)
            user = UserFactory.create()
            user.groups.add(group)
            user.refresh_from_db()
            for perm_description in self.expected_group_permissions[group_name]:
                perm = self.Permission.objects.get(content_type__app_label=perm_description[0],
                                                   content_type__model=perm_description[1],
                                                   codename__startswith=perm_description[2])
                perm_string = '.'.join((perm.content_type.app_label, perm.codename))
                if perm not in group.permissions.all():
                    msg = 'Group {} missing permission {}'.format(group_name, perm_string)
                    missing_permission_msgs.append(msg)
                if not user.has_perm(perm_string):
                    msg = 'User from group {} missing permission {}'.format(group_name, perm_string)
                    missing_permission_msgs.append(msg)
        self.assertEqual(len(missing_permission_msgs), 0, msg='\n'.join(missing_permission_msgs))
