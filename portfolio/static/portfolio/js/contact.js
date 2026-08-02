/**
 * contact.js — Contact page only.
 * Progressive enhancement over the plain Django form: submits via
 * fetch(), shows inline field errors, a loading spinner, and an
 * animated success/error banner. If JS is disabled or fetch fails
 * unexpectedly, the form still works as a normal POST (see the
 * "no-JS fallback" branch in portfolio/views.py::contact).
 */
(function () {
  var form = document.getElementById('contactForm');
  if (!form) return;

  var submitBtn    = document.getElementById('contactSubmit');
  var submitLabel  = form.querySelector('.contact-form__submit-label');
  var banner       = document.getElementById('contactBanner');
  var bannerIcon   = document.getElementById('contactBannerIcon');
  var bannerText   = document.getElementById('contactBannerText');
  var isSubmitting = false;

  var originalLabel = submitLabel ? submitLabel.textContent : 'Send Message';

  var SUCCESS_ICON =
    '<svg class="contact-form__banner-icon" viewBox="0 0 24 24" aria-hidden="true">' +
    '<circle class="contact-form__check-circle" cx="12" cy="12" r="10"></circle>' +
    '<path class="contact-form__check-mark" d="M7 12.5l3 3 7-7"></path>' +
    '</svg>';

  var ERROR_ICON =
    '<svg class="contact-form__banner-icon" viewBox="0 0 24 24" aria-hidden="true">' +
    '<circle class="contact-form__check-circle" cx="12" cy="12" r="10"></circle>' +
    '<path class="contact-form__check-mark" d="M8 8l8 8M16 8l-8 8"></path>' +
    '</svg>';

  // Mirrors the server-side rules in forms.py — purely for instant
  // feedback. The server remains the source of truth; every response
  // still runs through the same showFieldErrors()/showBanner() path.
  var CLIENT_RULES = {
    name: function (v) { return v.trim().length < 2 ? 'Please enter your full name.' : null; },
    email: function (v) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? null : 'Please enter a valid email address.';
    },
    subject: function (v) { return v.trim().length < 3 ? 'Please add a short subject for your message.' : null; },
    message: function (v) {
      if (v.trim().length < 10) return 'Your message is a little too short — please add more detail.';
      if (v.trim().length > 5000) return 'Your message is too long (5000 characters max).';
      return null;
    },
  };

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : null;
  }

  function showBanner(kind, text) {
    banner.classList.remove('contact-form__banner--success', 'contact-form__banner--error');
    banner.classList.add('contact-form__banner--' + kind, 'contact-form__banner--visible');
    bannerIcon.innerHTML = kind === 'success' ? SUCCESS_ICON : ERROR_ICON;
    bannerText.textContent = text;
    banner.setAttribute('role', kind === 'success' ? 'status' : 'alert');
    banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function clearFieldErrors() {
    form.querySelectorAll('.contact-form__error').forEach(function (el) {
      el.textContent = '';
    });
    form.querySelectorAll('.contact-form__input, .contact-form__textarea').forEach(function (el) {
      el.classList.remove('contact-form__input--error', 'contact-form__textarea--error');
      el.removeAttribute('aria-invalid');
    });
  }

  function showFieldErrors(errors) {
    Object.keys(errors).forEach(function (fieldName) {
      var input = form.querySelector('[name="' + fieldName + '"]');
      var errorEl = document.getElementById('error-' + fieldName);
      var message = errors[fieldName][0] && errors[fieldName][0].message
        ? errors[fieldName][0].message
        : 'This field has an issue — please check it.';

      if (errorEl) errorEl.textContent = message;
      if (input) {
        input.classList.add(
          input.tagName === 'TEXTAREA' ? 'contact-form__textarea--error' : 'contact-form__input--error'
        );
        input.setAttribute('aria-invalid', 'true');
      }
    });
  }

  // Client-side pre-check, run before the fetch. Returns a
  // { fieldName: [{message}] } map matching the server's shape, or
  // null if everything looks fine, so it can flow through the exact
  // same showFieldErrors()/showBanner() rendering path.
  function runClientValidation() {
    var errors = {};
    Object.keys(CLIENT_RULES).forEach(function (fieldName) {
      var input = form.querySelector('[name="' + fieldName + '"]');
      if (!input) return;
      var message = CLIENT_RULES[fieldName](input.value || '');
      if (message) errors[fieldName] = [{ message: message }];
    });
    return Object.keys(errors).length ? errors : null;
  }

  function setLoading(loading) {
    isSubmitting = loading;
    submitBtn.disabled = loading;
    submitBtn.classList.toggle('contact-form__submit--loading', loading);
    if (submitLabel) submitLabel.textContent = loading ? 'Sending…' : originalLabel;
  }

  // Subtle click ripple on the submit button. Purely decorative;
  // skipped entirely for prefers-reduced-motion.
  function spawnRipple(event) {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;

    var rect = submitBtn.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height) * 1.4;
    var ripple = document.createElement('span');
    ripple.className = 'contact-form__ripple';
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (event.clientX - rect.left - size / 2) + 'px';
    ripple.style.top = (event.clientY - rect.top - size / 2) + 'px';
    submitBtn.appendChild(ripple);
    window.setTimeout(function () {
      if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
    }, 650);
  }

  submitBtn.addEventListener('click', function (event) {
    // Only a decorative flourish — never blocks submission, and only
    // fires on real pointer clicks (has clientX/Y), not keyboard
    // Enter/Space activation.
    if (event.clientX || event.clientY) spawnRipple(event);
  });

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    // Prevent duplicate/double submissions while a request is in flight.
    if (isSubmitting) return;

    clearFieldErrors();
    banner.classList.remove('contact-form__banner--visible');

    var clientErrors = runClientValidation();
    if (clientErrors) {
      showFieldErrors(clientErrors);
      showBanner('error', 'Please fix the highlighted fields and try again.');
      return;
    }

    setLoading(true);

    var formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken'),
      },
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        setLoading(false);

        if (result.ok && result.data.success) {
          showBanner('success', result.data.message);
          form.reset();
          // Refresh the anti-spam timestamp for a possible second message.
          var tsField = form.querySelector('[name="form_rendered_at"]');
          fetch(form.dataset.timestampUrl)
            .then(function (r) { return r.json(); })
            .then(function (d) { if (tsField) tsField.value = d.timestamp; })
            .catch(function () { /* non-critical */ });
        } else if (result.data.errors) {
          showFieldErrors(result.data.errors);
          showBanner('error', 'Please fix the highlighted fields and try again.');
        } else {
          showBanner('error', 'Something went wrong — please try again in a moment.');
        }
      })
      .catch(function () {
        setLoading(false);
        // Network failure — let the browser fall back to a real POST
        // so the visitor's message still has a way to get through.
        showBanner('error', "Couldn't reach the server. Submitting the regular way…");
        window.setTimeout(function () {
          isSubmitting = false;
          HTMLFormElement.prototype.submit.call(form);
        }, 800);
      });
  });
})();
