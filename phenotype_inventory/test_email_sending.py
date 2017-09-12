"""Test sending of actual emails, but only on non-development systems."""


from time import sleep
import urllib.request
import urllib.error
from uuid import uuid4

from django.conf import settings
from django.core.mail import send_mail
from django.test.utils import override_settings
from django.test import TestCase


# Need to specify the email backend here, because Django always uses the
# internal memory backend for TestCase test environments.
@override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
class TestEmailSending(TestCase):

    def test_sending(self):
        """SMTP settings can actually send an email to a real email address.

        Uses a temp email address at Mailinator.com. This test may fail simply due to timing issues.
        """
        if settings.DEVELOPMENT:
            pass
        else:
            print('\nWarning: this test can take up to 10 minutes to run.')
            # Make a test email address at Mailinator.com.
            fake_name = str(uuid4())
            mailbox_name = fake_name
            email_address = "{}@mailinator.com".format(mailbox_name)
            email_subject = "subject-" + fake_name
            # Send email to the test address.
            send_mail(subject=email_subject,
                      message='Some message content',
                      from_email=settings.DEFAULT_FROM_EMAIL,
                      recipient_list=[email_address, ])
            # Check the feed for the fake email address.
            mailbox_feed = "http://mailinator.com/feed?to=" + mailbox_name
            expected_tag = "<title>{}</title>".format(email_subject)
            # Wait to make sure the email is actually received.
            print('Waiting for test email...')
            sleep(20)
            try:
                # The test may fail due to the vagaries of email delivery.
                # So check for the email in a loop.
                for idx in range(60):
                    request = urllib.request.Request(mailbox_feed, headers={'User-Agent': 'Mozilla/5.0'})
                    response = urllib.request.urlopen(request)
                    mailbox_data = response.read().decode('utf-8')
                    # Stop the checks once you've found the email.
                    if expected_tag in mailbox_data:
                        break
                    else:
                        sleep(10)
            except urllib.HttpError as error:
                if error.code == 429:
                    print('Too many requests to Mailinator. Skipping email test...')
                    raise
                else:
                    raise
            # print(mailbox_data)
            self.assertTrue(expected_tag in mailbox_data)
