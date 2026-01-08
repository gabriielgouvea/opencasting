(function () {
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
    ensurePushmenuButton();

    // Alguns temas re-renderizam header em navegações; observa mudanças por segurança.
    try {
      var header = document.querySelector('.main-header');
      if (!header) return;
      var mo = new MutationObserver(function () {
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
