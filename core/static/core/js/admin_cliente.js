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
      var isClienteList = body && body.classList && body.classList.contains('app-core') && body.classList.contains('model-cliente') && body.classList.contains('change-list');
      if (isClienteList) {
        // Remove links do topo específicos (Ver Site / Suporte Técnico)
        document.querySelectorAll('.main-header a.nav-link, .main-header a').forEach(function (a) {
          var t = String((a.textContent || '')).replace(/\s+/g, ' ').trim().toLowerCase();
          if (t.indexOf('ver site') >= 0 || t.indexOf('suporte') >= 0) {
            var li = a.closest ? a.closest('li') : null;
            if (li && li.parentNode) li.parentNode.removeChild(li);
          }
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
