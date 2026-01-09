(function () {
  function onlyDigits(value) {
    return String(value || '').replace(/\D+/g, '');
  }

  function formatCNPJ(raw) {
    var d = onlyDigits(raw);
    if (d.length > 14) d = d.slice(0, 14);
    if (d.length <= 2) return d;
    if (d.length <= 5) return d.slice(0, 2) + '.' + d.slice(2);
    if (d.length <= 8) return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5);
    if (d.length <= 12) return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5, 8) + '/' + d.slice(8);
    return d.slice(0, 2) + '.' + d.slice(2, 5) + '.' + d.slice(5, 8) + '/' + d.slice(8, 12) + '-' + d.slice(12);
  }

  function setValue(id, value) {
    var el = document.getElementById(id);
    if (!el) return;
    if (el.value && String(el.value).trim().length && String(value || '').trim().length) {
      // Não sobrescreve campos que o usuário já preencheu
      return;
    }
    el.value = value || '';
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function showInlineMessage(text, level) {
    var container = document.querySelector('.content .col-12, #content-main, .content');
    if (!container) return;

    var div = document.createElement('div');
    div.className = 'alert alert-' + (level || 'info');
    div.style.marginBottom = '12px';
    div.textContent = text;
    container.prepend(div);

    setTimeout(function () {
      try {
        div.remove();
      } catch (e) {
        // ignore
      }
    }, 4500);
  }

  async function fetchCNPJ(cnpjDigits) {
    var base = window.location.pathname;
    // Normaliza para o root do ModelAdmin: /admin/core/cliente/
    base = base.replace(/\/add\/?$/, '/');
    base = base.replace(/\/\d+\/change\/?$/, '/');
    if (!base.endsWith('/')) base += '/';
    var url = base + 'buscar-cnpj/?cnpj=' + encodeURIComponent(cnpjDigits);
    var resp = await fetch(url, { headers: { 'Accept': 'application/json' } });
    var json = await resp.json().catch(function () { return null; });
    if (!resp.ok || !json || !json.ok) {
      var msg = (json && json.error) ? json.error : 'Não foi possível consultar o CNPJ.';
      throw new Error(msg);
    }
    return json.data;
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Changelist: ajustes visuais e ação do menu ⋯
    try {
      var body = document.body;
      var isClienteList =
        body &&
        body.classList &&
        body.classList.contains('model-cliente') &&
        (body.classList.contains('change-list') || body.classList.contains('changelist'));
      if (isClienteList) {
        // Remove de vez o cabeçalho/breadcrumb (fallback caso o CSS do tema vença)
        var header = document.querySelector('.content-header');
        if (header && header.parentNode) {
          header.parentNode.removeChild(header);
        }

        // Remove links do topo específicos (Ver Site / Suporte Técnico)
        document.querySelectorAll('.main-header a.nav-link, .main-header a').forEach(function (a) {
          var t = String((a.textContent || '')).replace(/\s+/g, ' ').trim().toLowerCase();
          if (t.indexOf('ver site') >= 0 || t.indexOf('suporte') >= 0) {
            var li = a.closest ? a.closest('li') : null;
            if (li && li.parentNode) li.parentNode.removeChild(li);
          }
        });

        // Menu ⋯: flutuante (não corta por overflow) e abre pra cima quando necessário.
        document.querySelectorAll('details[data-oc-actions="1"]').forEach(function (d) {
          if (d.__ocActionsBound) return;
          d.__ocActionsBound = true;

          var menu = d.querySelector('.oc-actions__menu');
          var summary = d.querySelector('summary');
          if (!menu || !summary) return;

          // Guarda onde o menu estava para restaurar ao fechar
          if (!menu.__ocOriginalParent) {
            menu.__ocOriginalParent = menu.parentNode;
            menu.__ocNextSibling = menu.nextSibling;
          }

          function floatMenu() {
            if (!d.open) {
              d.classList.remove('oc-actions--up');
              // Restaura o menu para dentro do details
              if (menu.__ocFloating) {
                menu.__ocFloating = false;
                try {
                  menu.style.position = '';
                  menu.style.left = '';
                  menu.style.top = '';
                  menu.style.right = '';
                  menu.style.bottom = '';
                  menu.style.zIndex = '';
                  menu.style.width = '';
                } catch (e) {}
                try {
                  if (menu.__ocOriginalParent && menu.__ocOriginalParent.nodeType === 1) {
                    if (menu.__ocNextSibling && menu.__ocNextSibling.parentNode === menu.__ocOriginalParent) {
                      menu.__ocOriginalParent.insertBefore(menu, menu.__ocNextSibling);
                    } else {
                      menu.__ocOriginalParent.appendChild(menu);
                    }
                  }
                } catch (e2) {}
              }
              return;
            }

            d.classList.remove('oc-actions--up');

            // Mede o menu
            var prevDisplay = menu.style.display;
            var prevVisibility = menu.style.visibility;
            menu.style.visibility = 'hidden';
            menu.style.display = 'block';

            var menuRect = menu.getBoundingClientRect();
            var anchorRect = summary.getBoundingClientRect();
            var menuW = menuRect.width || 160;
            var menuH = menuRect.height || 120;

            // Restaura antes de mover
            menu.style.display = prevDisplay;
            menu.style.visibility = prevVisibility;

            // Move para o body para não ser cortado por overflow
            try {
              document.body.appendChild(menu);
              menu.__ocFloating = true;
            } catch (e3) {
              // Se não conseguir mover, ainda tenta posicionar via classe
            }

            // Calcula posição
            var margin = 8;
            var left = Math.max(margin, Math.min(anchorRect.right - menuW, window.innerWidth - menuW - margin));
            var downTop = anchorRect.bottom + 4;
            var upTop = anchorRect.top - menuH - 4;
            var useUp = (downTop + menuH > window.innerHeight - margin) && (upTop >= margin);

            if (useUp) d.classList.add('oc-actions--up');

            var top = useUp ? upTop : downTop;
            top = Math.max(margin, Math.min(top, window.innerHeight - menuH - margin));

            try {
              menu.style.position = 'fixed';
              menu.style.left = left + 'px';
              menu.style.top = top + 'px';
              menu.style.right = 'auto';
              menu.style.bottom = 'auto';
              menu.style.zIndex = '100000';
              menu.style.display = 'block';
            } catch (e4) {}
          }

          d.addEventListener('toggle', function () {
            window.setTimeout(function () {
              floatMenu();
            }, 0);
          });

          // Fecha ao clicar fora
          document.addEventListener('click', function (e) {
            if (!d.open) return;
            var t = e && e.target;
            if (!t) return;
            if ((t.closest && t.closest('details[data-oc-actions="1"]')) || (menu.contains && menu.contains(t))) {
              return;
            }
            try {
              d.open = false;
            } catch (e5) {}
          });

          // Fecha ao rolar para não ficar “solto”
          window.addEventListener('scroll', function () {
            if (!d.open) return;
            try {
              d.open = false;
            } catch (e6) {}
          }, true);
        });

        // Confirmação ao excluir por linha
        document.querySelectorAll('a[data-oc-delete="1"]').forEach(function (a) {
          if (a.__ocDeleteBound) return;
          a.__ocDeleteBound = true;
          a.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var ok = true;
            try {
              ok = window.confirm('Excluir este cliente?');
            } catch (e2) {}
            if (ok) {
              window.location.href = a.getAttribute('href');
            }
          });
        });
      }
    } catch (e) {
      // ignore
    }

    var cnpjInput = document.getElementById('id_cnpj');
    if (!cnpjInput) return;

    // Máscara simples
    cnpjInput.addEventListener('input', function () {
      var before = cnpjInput.value;
      var formatted = formatCNPJ(before);
      if (formatted !== before) cnpjInput.value = formatted;
    });

    var lastLookup = null;

    cnpjInput.addEventListener('blur', async function () {
      var digits = onlyDigits(cnpjInput.value);
      if (digits.length !== 14) return;
      if (lastLookup === digits) return;
      lastLookup = digits;

      try {
        var data = await fetchCNPJ(digits);
        setValue('id_razao_social', data.razao_social);
        setValue('id_nome_fantasia', data.nome_fantasia);
        setValue('id_data_abertura', data.data_abertura);
        setValue('id_situacao_cadastral', data.situacao_cadastral);
        setValue('id_natureza_juridica', data.natureza_juridica);
        setValue('id_cnae_principal', data.cnae_principal);
        setValue('id_cnae_principal_descricao', data.cnae_principal_descricao);
        setValue('id_cep', data.cep);
        setValue('id_logradouro', data.logradouro);
        setValue('id_numero', data.numero);
        setValue('id_complemento', data.complemento);
        setValue('id_bairro', data.bairro);
        setValue('id_cidade', data.cidade);
        setValue('id_uf', data.uf);
        setValue('id_telefone', data.telefone);

        showInlineMessage('Dados do CNPJ preenchidos automaticamente.', 'success');
      } catch (e) {
        showInlineMessage(e.message || 'Falha ao consultar CNPJ.', 'warning');
      }
    });
  });
})();
