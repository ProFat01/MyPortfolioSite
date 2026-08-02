/**
 * main.js — Portfolio JavaScript
 * Handles: navbar scroll effect, mobile menu, scroll-reveal (fade-up)
 * animations, and the light/dark theme toggle. (The hero entrance
 * animation on the Home page is pure CSS — see style.css — since it
 * always plays immediately on load rather than on scroll.)
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
// 3. Scroll-triggered fade-up / scroll-reveal animation
//    Any element with class "fade-up" animates in when it enters
//    the viewport (see .fade-up / .fade-up.visible in style.css).
//
//    IMPORTANT ORDERING: the classes below must be assigned to
//    elements BEFORE the IntersectionObserver scans the page for
//    ".fade-up" elements to watch — otherwise the observer would
//    run its query too early and miss everything that gets tagged
//    afterwards. Keeping both steps in one block guarantees the
//    order stays correct.
// ----------------------------------------------------------------
(function () {

  // --- Step 1: tag the elements we want to reveal on scroll -----

  // Home page — highlight/stat cards, staggered
  document.querySelectorAll('.highlight-card').forEach(function (card, index) {
    card.style.transitionDelay = (index * 0.08) + 's';
    card.classList.add('fade-up');
  });

  // Projects page — project cards, staggered
  document.querySelectorAll('.project-card').forEach(function (card, index) {
    card.style.transitionDelay = (index * 0.08) + 's';
    card.classList.add('fade-up');
  });

  // Contact page — contact cards, staggered
  document.querySelectorAll('.contact-card').forEach(function (card, index) {
    card.style.transitionDelay = (index * 0.1) + 's';
    card.classList.add('fade-up');
  });

  // Inner-page hero banners (About / Projects / Contact — the Home
  // page hero animates in immediately via CSS instead, see style.css)
  document.querySelectorAll('.page-hero__inner').forEach(function (el) {
    el.classList.add('fade-up');
  });

  // About page — image column and text column, gently staggered
  document.querySelectorAll('.about__image-col, .about__text-col').forEach(function (el, index) {
    el.style.transitionDelay = (index * 0.12) + 's';
    el.classList.add('fade-up');
  });

  // Contact page — info column and decorative quote panel
  document.querySelectorAll('.contact-info, .contact-deco').forEach(function (el, index) {
    el.style.transitionDelay = (index * 0.12) + 's';
    el.classList.add('fade-up');
  });

  // --- Step 2: observe every tagged element --------------------

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

  document.querySelectorAll('.fade-up').forEach(function (el) {
    observer.observe(el);
  });
})();


// ----------------------------------------------------------------
// 4. Light / Dark theme toggle
//    The INITIAL theme is already applied by the tiny inline script
//    in base.html's <head> (it has to run before first paint to
//    avoid a flash of the wrong theme). This block only wires up
//    the toggle button so the user can switch it, and remembers
//    their choice in localStorage under 'portfolio-theme'.
// ----------------------------------------------------------------
(function () {
  var STORAGE_KEY = 'portfolio-theme';
  var toggle = document.getElementById('themeToggle');
  if (!toggle) return;

  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    toggle.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      // Storage unavailable (private browsing, etc.) — toggle still
      // works for the current page view, it just won't persist.
    }
  }

  // Sync the button's aria-pressed state with whatever the inline
  // head script already applied on load.
  toggle.setAttribute('aria-pressed', currentTheme() === 'light' ? 'true' : 'false');

  toggle.addEventListener('click', function () {
    setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
  });

  // If the visitor hasn't explicitly chosen a theme on this site yet,
  // keep following their OS-level light/dark setting live.
  if (window.matchMedia) {
    var mql = window.matchMedia('(prefers-color-scheme: light)');
    var onSystemChange = function (e) {
      var stored = null;
      try { stored = localStorage.getItem(STORAGE_KEY); } catch (err) { /* ignore */ }
      if (!stored) setTheme(e.matches ? 'light' : 'dark');
    };
    // addEventListener is the modern API; addListener is the legacy
    // fallback for older Safari versions.
    if (mql.addEventListener) mql.addEventListener('change', onSystemChange);
    else if (mql.addListener) mql.addListener(onSystemChange);
  }
})();


// ----------------------------------------------------------------
// 5. Back-to-top button
//    Appears once the visitor has scrolled down a bit, and smoothly
//    scrolls back to the top of the page when clicked.
// ----------------------------------------------------------------
(function () {
  var btn = document.getElementById('backToTop');
  if (!btn) return;

  function onScroll() {
    if (window.scrollY > 400) {
      btn.classList.add('back-to-top--visible');
    } else {
      btn.classList.remove('back-to-top--visible');
    }
  }

  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  btn.addEventListener('click', function () {
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });
})();


// ----------------------------------------------------------------
// 6. Page loader
//    The loader is already visible the moment the page paints
//    (plain CSS default — see style.css "18. Page loader"), so it
//    can never be skipped by a slow or failed script. This block's
//    only jobs are:
//      a) hide it once the page has actually finished loading
//      b) never let it get stuck (hard failsafe timeout)
//      c) remember (sessionStorage) that the visitor has already
//         seen the full animation this session, so later page loads
//         within the same visit use a much shorter minimum display
//         time instead of the full first-visit one.
// ----------------------------------------------------------------
(function () {
  var loader = document.getElementById('pageLoader');
  if (!loader) return;

  var STORAGE_KEY = 'portfolio-loaded';
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var seenThisSession = false;
  try { seenThisSession = !!sessionStorage.getItem(STORAGE_KEY); } catch (e) {
    // sessionStorage unavailable (private browsing, etc.) — falls
    // back to treating every page as a "first visit", which is safe.
  }

  // Minimum time the loader stays visible, so it never reads as a
  // meaningless flicker even when the page loads instantly (e.g.
  // from cache). Reduced-motion visitors skip the minimum entirely.
  var minDisplay = reduceMotion ? 0 : (seenThisSession ? 150 : 600);
  var shownAt = Date.now();
  var hidden = false;

  function hideLoader() {
    if (hidden) return;
    hidden = true;

    loader.classList.add('page-loader--hidden');
    document.documentElement.classList.remove('is-loading');
    document.body.classList.remove('is-loading');

    try { sessionStorage.setItem(STORAGE_KEY, '1'); } catch (e) { /* ignore */ }

    // Remove it from the DOM once the fade-out transition finishes
    // (matches the 0.5s transition in style.css) so it stops taking
    // up space and can't intercept anything, even by accident.
    window.setTimeout(function () {
      if (loader.parentNode) loader.parentNode.removeChild(loader);
    }, 550);
  }

  function onReady() {
    var elapsed = Date.now() - shownAt;
    window.setTimeout(hideLoader, Math.max(0, minDisplay - elapsed));
  }

  if (document.readyState === 'complete') {
    onReady();
  } else {
    window.addEventListener('load', onReady);
  }

  // Hard failsafe: whatever happens above, the loader is never
  // allowed to block the site for more than a few seconds.
  window.setTimeout(hideLoader, 4000);
})();
