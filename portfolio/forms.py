"""
portfolio/forms.py
The public Contact form: field validation + two lightweight,
dependency-free spam defences (honeypot + minimum fill time).
"""

import time

from django import forms
from django.core.exceptions import ValidationError

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # ------------------------------------------------------------
    # Spam protection field #1: honeypot.
    # A real visitor never sees or fills this (hidden via CSS), so
    # any submission with it filled in is almost certainly a bot.
    # ------------------------------------------------------------
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'tabindex': '-1',
            'class': 'contact-form__honeypot',
            'aria-hidden': 'true',
        }),
    )

    # ------------------------------------------------------------
    # Spam protection field #2: timestamp the form was rendered.
    # Bots that auto-submit instantly get rejected; a human takes
    # at least a couple of seconds to read + type.
    # ------------------------------------------------------------
    form_rendered_at = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your full name',
                'autocomplete': 'name',
                'maxlength': '100',
                'class': 'contact-form__input',
                'required': 'required',
                'aria-describedby': 'error-name',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@example.com',
                'autocomplete': 'email',
                'class': 'contact-form__input',
                'required': 'required',
                'aria-describedby': 'error-email',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+234 800 000 0000 (optional)',
                'autocomplete': 'tel',
                'class': 'contact-form__input',
                'aria-describedby': 'error-phone',
            }),
            'subject': forms.TextInput(attrs={
                'placeholder': "What's this about?",
                'maxlength': '150',
                'class': 'contact-form__input',
                'required': 'required',
                'aria-describedby': 'error-subject',
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Tell me a bit more…',
                'rows': 6,
                'class': 'contact-form__textarea',
                'required': 'required',
                'aria-describedby': 'error-message',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise ValidationError("Please enter your full name.")
        return name

    def clean_subject(self):
        subject = self.cleaned_data['subject'].strip()
        if len(subject) < 3:
            raise ValidationError("Please add a short subject for your message.")
        return subject

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 10:
            raise ValidationError("Your message is a little too short — please add more detail.")
        if len(message) > 5000:
            raise ValidationError("Your message is too long (5000 characters max).")
        return message

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            digits = ''.join(ch for ch in phone if ch.isdigit())
            if len(digits) < 7:
                raise ValidationError("Please enter a valid phone number.")
        return phone

    def clean_website(self):
        # Honeypot: must always be empty.
        value = self.cleaned_data.get('website', '')
        if value:
            raise ValidationError("Spam detected.")
        return value

    def clean_form_rendered_at(self):
        rendered_at = self.cleaned_data['form_rendered_at']
        elapsed = time.time() - rendered_at
        if elapsed < 2:
            raise ValidationError("Please take a moment before submitting.")
        if elapsed > 3600:
            raise ValidationError("This form has expired — please reload the page and try again.")
        return rendered_at
