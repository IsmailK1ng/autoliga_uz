/* Desktop hero slider on the home page (>= 1200px). Markup: main/includes/hero_xl_body.html, styles: css/hero_xl.css.
   Without JavaScript the first slide shows and every rail card is a plain link to its model page.
   Autoplay has no JS timer: the active card's progress bar is a 6s CSS animation and its animationend
   moves to the next slide, so pausing is animation-play-state and leaving the breakpoint simply stops it. */
(function () {
    'use strict';

    var root = document.querySelector('.hero-xl');
    if (!root) return;

    var desktop = window.matchMedia('(min-width: 1200px)');
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    var slides = Array.prototype.slice.call(root.querySelectorAll('.hx-slide'));
    var cards = Array.prototype.slice.call(root.querySelectorAll('.hx-card'));
    var tabs = Array.prototype.slice.call(root.querySelectorAll('.hx-tab'));
    var list = root.querySelector('.hx-cards');
    var live = root.querySelector('.hx-slides');
    var counterCur = root.querySelector('.hx-counter__cur');
    var counterTotal = root.querySelector('.hx-counter__total');
    var current = 0;
    var filter = '';
    var hovered = false;
    var focused = false;
    var inView = !('IntersectionObserver' in window);  // off-screen: no autoplay, so no slide images load unseen

    function pad(n) {
        return (n < 10 ? '0' : '') + n;
    }

    // slide indexes of the current brand tab, in slider order
    function order() {
        return slides.map(function (s, i) { return i; }).filter(function (i) {
            return !filter || slides[i].getAttribute('data-brand') === filter;
        });
    }

    // the big image of a slide: fill srcset from data-srcset (only matches >= 1200px through <source media>)
    function loadImage(i) {
        var slide = slides[i];
        if (!slide) return;
        slide.querySelectorAll('source[data-srcset]').forEach(function (source) {
            source.setAttribute('srcset', source.getAttribute('data-srcset'));
            source.removeAttribute('data-srcset');
        });
        var img = slide.querySelector('.hx-car__img');
        if (img && img.loading === 'lazy') img.loading = 'eager';
    }

    function preloadNext() {
        if (!desktop.matches) return;
        var seq = order();
        var pos = seq.indexOf(current);
        if (seq.length > 1) loadImage(seq[(pos + 1) % seq.length]);
    }

    function autoplayAllowed() {
        return desktop.matches && !reduced.matches && order().length > 1;
    }

    function updatePlayState() {
        var playing = autoplayAllowed();
        var paused = hovered || focused || document.hidden || !inView;
        root.classList.toggle('is-playing', playing);
        root.classList.toggle('is-paused', paused);
        // announce slide changes only while nothing changes them automatically
        live.setAttribute('aria-live', playing && !paused ? 'off' : 'polite');
    }

    function restartProgress() {
        var bar = cards[current] && cards[current].querySelector('.hx-card__progress');
        if (!bar) return;
        bar.style.animation = 'none';
        void bar.offsetWidth;  // reflow, so the same animation starts again from 0
        bar.style.animation = '';
    }

    function updateCounter() {
        var seq = order();
        counterCur.textContent = pad(seq.indexOf(current) + 1);
        counterTotal.textContent = pad(seq.length);
    }

    // scroll only the rail (never the page) so the active card is fully visible
    function keepCardVisible() {
        var item = cards[current].parentNode;
        var left = item.offsetLeft - list.offsetLeft;
        var right = left + item.offsetWidth;
        var target = null;
        if (left < list.scrollLeft) target = left - 4;
        else if (right > list.scrollLeft + list.clientWidth) target = right - list.clientWidth + 4;
        if (target !== null) list.scrollTo({ left: target, behavior: reduced.matches ? 'auto' : 'smooth' });
    }

    function show(i) {
        if (i !== current) {
            var old = slides[current];
            old.classList.remove('is-active');
            old.setAttribute('aria-hidden', 'true');
            old.setAttribute('inert', '');
            cards[current].removeAttribute('aria-current');

            loadImage(i);
            var slide = slides[i];
            slide.classList.add('is-active');
            slide.removeAttribute('aria-hidden');
            slide.removeAttribute('inert');
            cards[i].setAttribute('aria-current', 'true');
            current = i;
        }
        updateCounter();
        keepCardVisible();
        restartProgress();
        preloadNext();
        updatePlayState();
    }

    function step(delta) {
        var seq = order();
        var pos = seq.indexOf(current);
        show(seq[(pos + delta + seq.length) % seq.length]);
    }

    root.querySelector('.hx-arrow--prev').addEventListener('click', function () { step(-1); });
    root.querySelector('.hx-arrow--next').addEventListener('click', function () { step(1); });

    cards.forEach(function (card, i) {
        card.addEventListener('click', function (e) {
            // keep new-tab / download clicks as normal links
            if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
            e.preventDefault();
            show(i);
        });
    });

    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            filter = tab.getAttribute('data-brand');
            tabs.forEach(function (t) { t.setAttribute('aria-pressed', t === tab ? 'true' : 'false'); });
            cards.forEach(function (card, i) {
                card.parentNode.hidden = !!filter && slides[i].getAttribute('data-brand') !== filter;
            });
            var seq = order();
            list.scrollLeft = 0;
            show(seq.indexOf(current) === -1 || filter ? seq[0] : current);
        });
    });

    root.addEventListener('animationend', function (e) {
        if (e.animationName === 'hx-progress' && root.classList.contains('is-playing')) step(1);
    });

    root.addEventListener('mouseenter', function () { hovered = true; updatePlayState(); });
    root.addEventListener('mouseleave', function () { hovered = false; updatePlayState(); });
    root.addEventListener('focusin', function (e) {
        // keyboard focus pauses; a mouse click on a button does not keep it paused after the pointer leaves
        focused = !e.target.matches || e.target.matches(':focus-visible');
        updatePlayState();
    });
    root.addEventListener('focusout', function (e) {
        if (!root.contains(e.relatedTarget)) {
            focused = false;
            updatePlayState();
        }
    });
    document.addEventListener('visibilitychange', updatePlayState);
    if (!inView) {
        new IntersectionObserver(function (entries) {
            inView = entries[entries.length - 1].isIntersecting;
            updatePlayState();
        }, { threshold: 0.35 }).observe(root);
    }

    function onBreakpoint() {
        if (desktop.matches) {
            preloadNext();
            restartProgress();
        }
        updatePlayState();
    }
    desktop.addEventListener('change', onBreakpoint);
    reduced.addEventListener('change', updatePlayState);

    root.classList.add('is-ready');
    updateCounter();
    updatePlayState();
    if (document.readyState === 'complete') preloadNext();
    else window.addEventListener('load', preloadNext, { once: true });
})();
