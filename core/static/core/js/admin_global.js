(function () {
  function isDesktop() {
    // AdminLTE costuma considerar >= 992px como layout desktop
    return (window.innerWidth || 0) >= 992;
  }

  function keepSidebarOpen() {
    if (!isDesktop()) return;

    try {
      var body = document.body;
      if (!body) return;

      // No desktop, sidebar aberta = sem 'sidebar-collapse'
      body.classList.remove('sidebar-collapse');
      body.classList.remove('sidebar-closed');
      body.classList.add('sidebar-open');
    } catch (e) {
      // ignore
    }
  }

  function ensurePushmenuButton() {
    try {
      var header = document.querySelector('.main-header');
      if (!header) return;

      // Se já existir, não faz nada
      var existing = header.querySelector('.nav-link[data-widget="pushmenu"]');
      if (existing) {
        // Alguns temas podem esconder via CSS; reforça visibilidade sem mexer em layout.
        existing.style.display = 'inline-flex';
        return;
      }

      // Tenta achar a UL padrão da navbar do tema
      var nav = header.querySelector('.navbar-nav');
      if (!nav) return;

      // Cria o item do menu (hamburger) compatível com AdminLTE/Jazzmin
      var li = document.createElement('li');
      li.className = 'nav-item';
      li.innerHTML =
        '<a class="nav-link" data-widget="pushmenu" href="#" role="button" aria-label="Menu">' +
        '<i class="fas fa-bars"></i>' +
        '</a>';

      nav.insertBefore(li, nav.firstChild);
    } catch (e) {
      // ignore
    }
  }

  function boot() {
    keepSidebarOpen();
    ensurePushmenuButton();

    // Se clicarem no hamburger no desktop, mantém aberto (não deixa colapsar)
    document.addEventListener(
      'click',
      function (e) {
        var t = e && e.target;
        if (!t) return;
        var a = t.closest ? t.closest('a[data-widget="pushmenu"]') : null;
        if (!a) return;
        if (!isDesktop()) return;
        e.preventDefault();
        e.stopPropagation();
        keepSidebarOpen();
      },
      true
    );

    // Se alguma rotina do tema tentar colapsar, desfaz
    try {
      var body = document.body;
      if (body) {
        var bodyObserver = new MutationObserver(function () {
          keepSidebarOpen();
        });
        bodyObserver.observe(body, { attributes: true, attributeFilter: ['class'] });
      }
    } catch (e) {
      // ignore
    }

    // Alguns temas re-renderizam header em navegações; observa mudanças por segurança.
    try {
      var header = document.querySelector('.main-header');
      if (!header) return;
      var mo = new MutationObserver(function () {
        keepSidebarOpen();
        ensurePushmenuButton();
      });
      mo.observe(header, { childList: true, subtree: true });
    } catch (e) {
      // ignore
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
