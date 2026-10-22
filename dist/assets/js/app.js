/* AANAK ACADEMY — vanilla UI runtime. No frameworks, no external requests. */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------------------------------------------------- 1. Mega menu */
  function initNav() {
    var toggle = $(".nav-toggle");
    var nav = $("#primary-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var open = nav.getAttribute("data-open") === "true";
        nav.setAttribute("data-open", String(!open));
        toggle.setAttribute("aria-expanded", String(!open));
      });
    }
    $$(".nav__item--has-panel").forEach(function (item) {
      var trigger = $(".nav__link", item);
      if (!trigger) return;
      var close = function () { item.setAttribute("data-open", "false"); trigger.setAttribute("aria-expanded", "false"); };
      var open = function () { item.setAttribute("data-open", "true"); trigger.setAttribute("aria-expanded", "true"); };
      trigger.addEventListener("click", function (e) {
        e.preventDefault();
        var isOpen = item.getAttribute("data-open") === "true";
        $$(".nav__item--has-panel").forEach(function (o) {
          o.setAttribute("data-open", "false");
          var t = $(".nav__link", o); if (t) t.setAttribute("aria-expanded", "false");
        });
        if (!isOpen) open();
      });
      item.addEventListener("mouseenter", function () { if (window.matchMedia("(min-width:1081px)").matches) open(); });
      item.addEventListener("mouseleave", function () { if (window.matchMedia("(min-width:1081px)").matches) close(); });
      item.addEventListener("keydown", function (e) { if (e.key === "Escape") { close(); trigger.focus(); } });
    });
    document.addEventListener("click", function (e) {
      if (e.target.closest(".nav__item--has-panel")) return;
      $$(".nav__item--has-panel").forEach(function (o) {
        o.setAttribute("data-open", "false");
        var t = $(".nav__link", o); if (t) t.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ------------------------------------------------ 2. ARIA tablists */
  function initTabs() {
    $$(".sub-specialty-tabs").forEach(function (root) {
      var tabs = $$('[role="tab"]', root);
      var panels = $$('[role="tabpanel"]', root);
      if (!tabs.length) return;
      function select(i, focus) {
        tabs.forEach(function (t, n) {
          t.setAttribute("aria-selected", String(n === i));
          t.setAttribute("tabindex", n === i ? "0" : "-1");
        });
        panels.forEach(function (p, n) { p.hidden = n !== i; });
        if (focus) tabs[i].focus();
      }
      tabs.forEach(function (tab, i) {
        tab.addEventListener("click", function () { select(i, false); });
        tab.addEventListener("keydown", function (e) {
          /* RTL: ArrowLeft advances, ArrowRight goes back */
          var n = null;
          if (e.key === "ArrowLeft") n = (i + 1) % tabs.length;
          else if (e.key === "ArrowRight") n = (i - 1 + tabs.length) % tabs.length;
          else if (e.key === "Home") n = 0;
          else if (e.key === "End") n = tabs.length - 1;
          if (n !== null) { e.preventDefault(); select(n, true); }
        });
      });
      select(0, false);
    });
  }

  /* ------------------------------------- 3. Instructor / course filters */
  function matches(card, state) {
    return Object.keys(state).every(function (key) {
      var want = state[key];
      if (!want || want === "all") return true;
      var have = (card.getAttribute("data-" + key) || "").split(" ");
      return have.indexOf(want) !== -1;
    });
  }
  function initFilters() {
    $$("[data-filter-root]").forEach(function (root) {
      var cards = $$("[data-filter-card]", root);
      var empty = $(".finder-empty", root);
      var state = {};
      $$(".filter-chip", root).forEach(function (chip) {
        chip.addEventListener("click", function () {
          var key = chip.getAttribute("data-filter-key");
          var val = chip.getAttribute("data-filter-value");
          var group = $$('.filter-chip[data-filter-key="' + key + '"]', root);
          var already = chip.getAttribute("aria-pressed") === "true";
          group.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
          if (already) { state[key] = "all"; }
          else { chip.setAttribute("aria-pressed", "true"); state[key] = val; }
          var shown = 0;
          cards.forEach(function (card) {
            var ok = matches(card, state);
            card.hidden = !ok;
            if (ok) shown++;
          });
          if (empty) empty.setAttribute("data-visible", shown === 0 ? "true" : "false");
        });
      });
    });
  }

  /* --------------------------------------------- 4. Dialogs / modals */
  function initDialogs() {
    $$("[data-dialog-open]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var dlg = document.querySelector(btn.getAttribute("data-dialog-open"));
        if (!dlg) return;
        if (typeof dlg.showModal === "function") dlg.showModal();
        else dlg.setAttribute("open", "");
        var first = dlg.querySelector("input, select, textarea, button");
        if (first) first.focus();
      });
    });
    $$("[data-dialog-close]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var dlg = btn.closest("dialog");
        if (!dlg) return;
        if (typeof dlg.close === "function") dlg.close(); else dlg.removeAttribute("open");
      });
    });
    $$("dialog.modal").forEach(function (dlg) {
      dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    });
  }

  /* --------------------------------- 5. Jump-pill scroll-spy (cheap) */
  function initScrollSpy() {
    var pills = $$(".jump-pills a");
    if (!pills.length || !("IntersectionObserver" in window)) return;
    var map = {};
    pills.forEach(function (p) {
      var id = p.getAttribute("href");
      if (id && id.charAt(0) === "#") { var el = document.querySelector(id); if (el) map[id] = { pill: p, el: el }; }
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var key = "#" + en.target.id;
        if (map[key]) map[key].pill.setAttribute("aria-current", en.isIntersecting ? "true" : "false");
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(map).forEach(function (k) { io.observe(map[k].el); });
  }

  /* --------------------------- 6. Context-aware mobile conversion bar */
  function initConversionBar() {
    var slot = $("[data-mcb-context]");
    if (!slot) return;
    var path = window.location.pathname;
    var label = slot.getAttribute("data-default-label") || "استعلام شهریه";
    var href = slot.getAttribute("data-default-href") || "/contact/#channels";
    var icon = "💬";
    if (path.indexOf("/art-cafe/") === 0 || path.indexOf("/music/") === 0) {
      label = "رزرو میز کافه"; href = "/art-cafe/#reservation"; icon = "🎹";
    } else if (path.indexOf("/performing-arts/") === 0 || path.indexOf("/acting-audition/") === 0) {
      label = "ثبت‌نام تست بازیگری"; href = "/acting-audition/#booking"; icon = "🎭";
    }
    slot.setAttribute("href", href);
    var t = $(".mcb__label", slot); if (t) t.textContent = label;
    var i = $(".mcb__icon", slot); if (i) i.textContent = icon;
  }

  function boot() {
    initNav(); initTabs(); initFilters(); initDialogs(); initScrollSpy(); initConversionBar();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
