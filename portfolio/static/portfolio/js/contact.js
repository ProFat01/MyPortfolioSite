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

  var submitBtn   = document.getElementById('contactSubmit');
  var banner      = document.getElementById('contactBanner');
  var bannerIcon  = document.getElementById('contactBannerIcon');
  var bannerText  = document.getElementById('contactBannerText');
  var isSubmitting = false;

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

  function setLoading(loading) {
    isSubmitting = loading;
    submitBtn.disabled = loading;
    submitBtn.classList.toggle('contact-form__submit--loading', loading);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    // Prevent duplicate/double submissions while a request is in flight.
    if (isSubmitting) return;

    clearFieldErrors();
    banner.classList.remove('contact-form__banner--visible');
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
