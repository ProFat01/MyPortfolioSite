"""
portfolio/views.py
One view function per page. Each fetches data from the database
and passes it to the matching HTML template.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils import timezone

from .models import Profile, Project
from .forms import ContactForm

logger = logging.getLogger(__name__)


def get_profile():
    """
    Helper: returns the first Profile object, or None if none exists yet.
    Used by every view so we don't repeat the same query everywhere.
    """
    return Profile.objects.first()


# ------------------------------------------------------------------
# Home page  →  /
# ------------------------------------------------------------------
def home(request):
    """
    Displays the hero section with the owner's name, title, and a short
    welcome message pulled from the Profile model.
    """
    profile = get_profile()
    context = {
        'profile': profile,
        'page': 'home',          # used to highlight the active nav link
        'meta_description': (
            profile.bio[:155] if profile and profile.bio
            else "Portfolio and selected work."
        ),
    }
    return render(request, 'portfolio/home.html', context)


# ------------------------------------------------------------------
# About page  →  /about/
# ------------------------------------------------------------------
def about(request):
    """
    Displays the full bio and social links from the Profile model.
    """
    profile = get_profile()
    context = {
        'profile': profile,
        'page': 'about',
        'meta_description': (
            profile.bio[:155] if profile and profile.bio
            else "Learn more about my background, skills, and experience."
        ),
    }
    return render(request, 'portfolio/about.html', context)


# ------------------------------------------------------------------
# Projects page  →  /projects/
# ------------------------------------------------------------------
def projects(request):
    """
    Fetches ALL Project records (newest first, controlled by model Meta ordering)
    and passes them to the template as a list.
    """
    all_projects = Project.objects.all()  # QuerySet of every project
    profile      = get_profile()
    context = {
        'projects': all_projects,
        'profile':  profile,
        'page':     'projects',
        'meta_description': "A selection of projects I've designed and built.",
    }
    return render(request, 'portfolio/projects.html', context)


# ------------------------------------------------------------------
# Contact page  →  /contact/
# ------------------------------------------------------------------
def contact(request):
    """
    Shows contact links AND a validated contact form.

    GET  → renders an empty form.
    POST → validates the form; on success, saves the enquiry, emails a
           notification to the site owner, optionally emails a
           confirmation to the visitor, and responds either with JSON
           (for the JS-driven AJAX flow) or a redirect (no-JS fallback).
    """
    profile = get_profile()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = ContactForm(request.POST)

        if form.is_valid():
            contact_message = form.save()
            _send_contact_emails(contact_message)

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': "Thanks — your message has been sent. I'll get back to you soon.",
                })

            messages.success(request, "Thanks — your message has been sent. I'll get back to you soon.")
            return redirect('portfolio:contact')

        # --- Invalid submission -----------------------------------
        if is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(escape_html=True),
            }, status=400)

        # No-JS fallback: fall through and re-render the page with errors.
    else:
        form = ContactForm(initial={'form_rendered_at': timezone.now().timestamp()})

    context = {
        'profile': profile,
        'page': 'contact',
        'form': form,
        'meta_description': "Get in touch — I'm always open to new projects and opportunities.",
    }
    return render(request, 'portfolio/contact.html', context)


def contact_form_timestamp(request):
    """
    Lightweight JSON endpoint the contact page's JS calls after the DOM
    is ready, so the anti-spam "minimum fill time" is measured from real
    render time even if the page was served from a cache.
    """
    return JsonResponse({'timestamp': timezone.now().timestamp()})


def _send_contact_emails(contact_message):
    """
    Sends the owner notification email (always) and the visitor
    confirmation email (if CONTACT_SEND_CONFIRMATION is enabled).
    Failures are logged rather than raised, so a broken mail server
    never breaks the visitor's experience — the message is already
    safely stored in the database either way.
    """
    site_name = getattr(settings, 'SITE_NAME', 'My Portfolio')
    owner_name = getattr(settings, 'CONTACT_OWNER_NAME', site_name)
    owner_email = getattr(settings, 'CONTACT_RECIPIENT_EMAIL', settings.DEFAULT_FROM_EMAIL)

    ctx = {
        'contact': contact_message,
        'site_name': site_name,
        'owner_name': owner_name,
    }

    # --- Notification to the site owner ---------------------------
    try:
        text_body = render_to_string('portfolio/emails/notification.txt', ctx)
        html_body = render_to_string('portfolio/emails/notification.html', ctx)

        email = EmailMultiAlternatives(
            subject=f"[{site_name}] New contact form message: {contact_message.subject}",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[owner_email],
            reply_to=[contact_message.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

        contact_message.notified = True
        contact_message.save(update_fields=['notified'])
    except Exception:
        logger.exception("Failed to send contact notification email for ContactMessage id=%s", contact_message.pk)

    # --- Confirmation to the visitor (optional) --------------------
    if getattr(settings, 'CONTACT_SEND_CONFIRMATION', True):
        try:
            text_body = render_to_string('portfolio/emails/confirmation.txt', ctx)
            html_body = render_to_string('portfolio/emails/confirmation.html', ctx)

            confirmation = EmailMultiAlternatives(
                subject=f"Thanks for reaching out, {contact_message.name.split()[0]}!",
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[contact_message.email],
            )
            confirmation.attach_alternative(html_body, "text/html")
            confirmation.send(fail_silently=False)
        except Exception:
            logger.exception("Failed to send contact confirmation email for ContactMessage id=%s", contact_message.pk)


# ------------------------------------------------------------------
# robots.txt  →  /robots.txt
# ------------------------------------------------------------------
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
