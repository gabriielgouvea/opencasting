(function () {
  function isDesktop() {
    return (window.innerWidth || 0) >= 992;
  }

  function setExpandedState() {
    if (!isDesktop()) return;

    var body = document.body;
    if (!body) return;

    // Marca para CSS reforçar o estado expandido
    body.classList.add('oc-sidebar-expanded');

    // Remove modos que causam "ícones apenas" e expansão por hover
    body.classList.remove('sidebar-collapse');
    body.classList.remove('sidebar-closed');
    body.classList.remove('sidebar-is-opening');

    // Remove variantes do "mini"
    try {
      var toRemove = [];
      body.classList.forEach(function (cls) {
        if (typeof cls === 'string' && cls.indexOf('sidebar-mini') === 0) {
          toRemove.push(cls);
        }
      });
      toRemove.forEach(function (cls) {
        body.classList.remove(cls);
      });
    } catch (e) {
      // ignore
    }

    // Evita persistência do estado colapsado (chaves comuns)
    try {
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

  function boot() {
    setExpandedState();

    // Se o tema tentar mudar classes depois, reverte
    try {
      var body = document.body;
      if (body) {
        var mo = new MutationObserver(function () {
          setExpandedState();
        });
        mo.observe(body, { attributes: true, attributeFilter: ['class'] });
      }
    } catch (e) {
      // ignore
    }

    try {
      window.addEventListener('resize', function () {
        setExpandedState();
      });
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
