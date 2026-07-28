"""
portfolio/models.py
Defines the two database models: Profile and Project.
"""

from django.db import models


class Profile(models.Model):
    """
    Stores the owner's personal information shown on the Home and About pages.
    Only ONE profile record is expected (your personal profile).
    """
    name  = models.CharField(max_length=100, help_text="Your full name")
    title = models.CharField(max_length=150, help_text="e.g. Full-Stack Developer")
    bio   = models.TextField(help_text="A paragraph or two about yourself")

    # upload_to places images inside media/profile_images/
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,   # optional — site won't break without a photo
        null=True,
    )

    # Social / contact links (all optional)
    github_url   = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    email        = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name  # shown in the Django admin list view

    class Meta:
        verbose_name_plural = "Profile"  # tidy label in admin


class Project(models.Model):
    """
    Represents a single portfolio project displayed on the Projects page.
    """
    title       = models.CharField(max_length=200)
    description = models.TextField(help_text="What the project does and the tech used")

    # upload_to places images inside media/project_images/
    image = models.ImageField(
        upload_to='project_images/',
        blank=True,
        null=True,
    )

    link       = models.URLField(blank=True, null=True, help_text="Live URL or GitHub repo")
    created_at = models.DateTimeField(auto_now_add=True)  # set automatically on creation

    def __str__(self):
        return self.title

    class Meta:
        # Newest projects shown first
        ordering = ['-created_at']


class ContactMessage(models.Model):
    """
    Stores every message submitted through the public Contact form.
    Acts as a durable backup of every enquiry — even if outbound email
    (notification/confirmation) fails for any reason, nothing is lost
    and the message can still be reviewed from the admin panel.
    """
    name    = models.CharField(max_length=100)
    email   = models.EmailField()
    phone   = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # True if the notification email to the site owner was sent successfully.
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.subject}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact message"
        verbose_name_plural = "Contact messages"
