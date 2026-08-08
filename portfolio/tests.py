"""
portfolio/tests.py

Tests for:
  - Feature 1: optional project presentation download button
  - Feature 2: redesigned contact CTA (Book a Meeting / Send Email)
    and footer social links.
"""

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Profile, Project

# Isolate any files created during these tests from the real media/ folder.
TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="portfolio_test_media_")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ProjectPresentationTests(TestCase):
    """Feature 1: optional 'Download Presentation' button."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_project_without_presentation_has_no_download_button(self):
        Project.objects.create(
            title="No Deck Project",
            description="A project with no presentation attached.",
        )
        response = self.client.get(reverse('portfolio:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Download Presentation")

    def test_project_with_presentation_shows_download_button(self):
        fake_pdf = SimpleUploadedFile(
            "deck.pdf", b"%PDF-1.4 fake content", content_type="application/pdf"
        )
        project = Project.objects.create(
            title="Deck Project",
            description="A project with a presentation attached.",
            presentation=fake_pdf,
        )
        response = self.client.get(reverse('portfolio:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Download Presentation")
        self.assertContains(response, project.presentation.url)

    def test_presentation_url_uses_media_url(self):
        from django.conf import settings

        fake_pdf = SimpleUploadedFile(
            "deck2.pdf", b"%PDF-1.4 fake content", content_type="application/pdf"
        )
        project = Project.objects.create(
            title="Deck Project 2",
            description="Checks the generated URL respects MEDIA_URL.",
            presentation=fake_pdf,
        )
        self.assertTrue(project.presentation.url.startswith(settings.MEDIA_URL))
        self.assertIn("project_presentations/", project.presentation.url)


class ContactCTATests(TestCase):
    """Feature 2: contact page CTA and footer social links."""

    def setUp(self):
        self.profile = Profile.objects.create(
            name="Saidu",
            title="Regulatory & Digital Professional",
            bio="Bio text.",
            github_url="https://github.com/example",
            linkedin_url="https://linkedin.com/in/example",
            email="saidu@example.com",
        )

    def test_contact_cta_renders(self):
        response = self.client.get(reverse('portfolio:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Have a project in mind? Let's talk.")

    @override_settings(GOOGLE_CALENDAR_BOOKING_URL="")
    def test_book_a_meeting_hidden_when_not_configured(self):
        response = self.client.get(reverse('portfolio:contact'))
        self.assertNotContains(response, "Book a Meeting")

    @override_settings(
        GOOGLE_CALENDAR_BOOKING_URL="https://calendar.google.com/calendar/appointments/schedules/example"
    )
    def test_book_a_meeting_uses_configured_url(self):
        response = self.client.get(reverse('portfolio:contact'))
        self.assertContains(response, "Book a Meeting")
        self.assertContains(
            response,
            'https://calendar.google.com/calendar/appointments/schedules/example',
        )
        self.assertContains(response, 'target="_blank"')

    def test_send_email_points_to_existing_contact_form(self):
        response = self.client.get(reverse('portfolio:contact'))
        self.assertContains(response, 'href="#contactForm"')
        # The form itself still carries that same id — no second form created.
        self.assertContains(response, 'id="contactForm"')
        self.assertEqual(
            response.content.decode().count('id="contactForm"'), 1,
            "There should be exactly one element with id='contactForm'.",
        )

    def test_footer_retains_github_linkedin_email_links(self):
        response = self.client.get(reverse('portfolio:contact'))
        self.assertContains(response, self.profile.github_url)
        self.assertContains(response, self.profile.linkedin_url)
        self.assertContains(response, f"mailto:{self.profile.email}")
