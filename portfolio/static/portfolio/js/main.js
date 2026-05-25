/**
 * main.js — Portfolio JavaScript
 * Handles: navbar scroll effect, mobile menu, fade-up animations
 */

// ----------------------------------------------------------------
// 1. Navbar: add .navbar--scrolled class when user scrolls down
// ----------------------------------------------------------------
(function () {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  function onScroll() {
    if (window.scrollY > 20) {
      navbar.classList.add('navbar--scrolled');
    } else {
      navbar.classList.remove('navbar--scrolled');
    }
  }

  // Run once on load in case page starts scrolled
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
})();


// ----------------------------------------------------------------
// 2. Mobile hamburger menu toggle
// ----------------------------------------------------------------
(function () {
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  if (!toggle || !links) return;

  toggle.addEventListener('click', function () {
    // Toggle open class on both button (for X animation) and nav links
    const isOpen = links.classList.toggle('open');
    toggle.classList.toggle('open', isOpen);
    // Accessibility: tell screen readers whether menu is expanded
    toggle.setAttribute('aria-expanded', isOpen);
  });

  // Close menu when a link is clicked (for single-page feel)
  links.querySelectorAll('.navbar__link').forEach(function (link) {
    link.addEventListener('click', function () {
      links.classList.remove('open');
      toggle.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
})();


// ----------------------------------------------------------------
// 3. Scroll-triggered fade-up animation
//    Any element with class "fade-up" will animate when it enters
//    the viewport. Add class="fade-up" to any HTML element you want
//    to animate in.
// ----------------------------------------------------------------
(function () {
  // IntersectionObserver is supported by all modern browsers
  if (!('IntersectionObserver' in window)) {
    // Fallback: just make everything visible immediately
    document.querySelectorAll('.fade-up').forEach(function (el) {
      el.classList.add('visible');
    });
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          // Stop watching once visible (animation plays once)
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.12,       // trigger when 12 % of element is visible
      rootMargin: '0px 0px -40px 0px',  // trigger slightly before bottom edge
    }
  );

  // Observe every element that has the fade-up class
  document.querySelectorAll('.fade-up').forEach(function (el) {
    observer.observe(el);
  });
})();


// ----------------------------------------------------------------
// 4. Stagger delay helper for project cards
//    Adds a small CSS animation-delay to each card so they
//    cascade in one-by-one instead of all at once.
// ----------------------------------------------------------------
(function () {
  document.querySelectorAll('.project-card').forEach(function (card, index) {
    // Each card gets a slightly longer delay than the previous
    card.style.transitionDelay = (index * 0.07) + 's';
    // Also add fade-up so the IntersectionObserver handles them
    card.classList.add('fade-up');
  });

  // Also stagger highlight cards on the home page
  document.querySelectorAll('.highlight-card').forEach(function (card, index) {
    card.style.transitionDelay = (index * 0.08) + 's';
    card.classList.add('fade-up');
  });

  // Stagger contact cards
  document.querySelectorAll('.contact-card').forEach(function (card, index) {
    card.style.transitionDelay = (index * 0.1) + 's';
    card.classList.add('fade-up');
  });
})();
