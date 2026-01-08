(function () {
  var enforceTimer = null;

  function isDesktop() {
    // AdminLTE costuma considerar >= 992px como layout desktop
    return (window.innerWidth || 0) >= 992;
  }

  function clearSidebarRememberState() {
    try {
      // Chaves comuns em temas/AdminLTE para lembrar colapso
      var keys = [
        'sidebar-collapse',
        'sidebarCollapsed',
        'adminlte-sidebar',
        'AdminLTE:sidebar',
        'AdminLTE:PushMenu',
        'pushmenu',
      ];
      keys.forEach(function (k) {
        try {
          window.localStorage && window.localStorage.removeItem(k);
        } catch (_e) {
          // ignore
        }
      });
    } catch (e) {
      // ignore
    }
  }

  function keepSidebarExpanded() {
    if (!isDesktop()) return;

    try {
      var body = document.body;
      if (!body) return;

      // No desktop, sidebar aberta = sem 'sidebar-collapse' (que ativa o modo hover)
      body.classList.remove('sidebar-collapse');
      body.classList.remove('sidebar-closed');
      body.classList.remove('sidebar-is-opening');
      // 'sidebar-open' é mais usado no mobile/overlay; no desktop pode atrapalhar.
      body.classList.remove('sidebar-open');
    } catch (e) {
      // ignore
    }
  }

  function startEnforceSidebar() {
    if (!isDesktop()) {
      if (enforceTimer) {
        clearInterval(enforceTimer);
        enforceTimer = null;
      }
      return;
    }

    if (enforceTimer) return;
    enforceTimer = setInterval(function () {
      keepSidebarExpanded();
    }, 300);
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
    clearSidebarRememberState();
    keepSidebarExpanded();
    startEnforceSidebar();
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
        keepSidebarExpanded();
      },
      true
    );

    // Se alguma rotina do tema tentar colapsar, desfaz
    try {
      var body = document.body;
      if (body) {
        var bodyObserver = new MutationObserver(function () {
          keepSidebarExpanded();
        });
        bodyObserver.observe(body, { attributes: true, attributeFilter: ['class'] });
      }
    } catch (e) {
      // ignore
    }

    // Se a pessoa redimensionar a janela, aplica a regra novamente
    try {
      window.addEventListener('resize', function () {
        clearSidebarRememberState();
        keepSidebarExpanded();
        startEnforceSidebar();
      });
    } catch (e) {
      // ignore
    }

    // Alguns temas re-renderizam header em navegações; observa mudanças por segurança.
    try {
      var header = document.querySelector('.main-header');
      if (!header) return;
      var mo = new MutationObserver(function () {
        keepSidebarExpanded();
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
