(function () {
  function isDesktop() {
    return (window.innerWidth || 0) >= 992;
  }

  function setJazzyMenuOpenCookie() {
    try {
      // Jazzmin usa o cookie 'jazzy_menu' para decidir se aplica 'sidebar-collapse' no <body>.
      // Se estiver 'closed', vira modo mini + hover. Mantemos sempre 'open'.
      var maxAge = 60 * 60 * 24 * 365; // 1 ano
      if (document.cookie && document.cookie.indexOf('jazzy_menu=open') !== -1) return;
      document.cookie = 'jazzy_menu=open; Max-Age=' + maxAge + '; SameSite=Lax; path=/';
    } catch (e) {
      // ignore
    }
  }

  function expandSidebarNow() {
    if (!isDesktop()) return;
    var body = document.body;
    if (!body) return;
    // Só remove as classes que colapsam/fecham (sem mexer em sidebar-mini)
    body.classList.remove('sidebar-collapse');
    body.classList.remove('sidebar-closed');
    body.classList.remove('sidebar-is-opening');
  }

  function boot() {
    setJazzyMenuOpenCookie();
    expandSidebarNow();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
