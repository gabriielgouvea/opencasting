(function () {
  function onlyDigits(value) {
    return String(value || '').replace(/\D+/g, '');
  }

  function formatPhoneBR(rawDigits) {
    var d = onlyDigits(rawDigits);
    if (!d) return '';

    // Remove prefixo 55 se usuário colar com país
    if (d.length > 11 && d.startsWith('55')) d = d.slice(2);

    var ddd = d.slice(0, 2);
    var rest = d.slice(2);
    var isMobile = rest.length >= 9;

    var first = isMobile ? rest.slice(0, 5) : rest.slice(0, 4);
    var second = isMobile ? rest.slice(5, 9) : rest.slice(4, 8);

    var out = '';
    if (ddd.length) out += '(' + ddd;
    if (ddd.length === 2) out += ') ';

    out += first;
    if (second.length) out += '-' + second;
    return out;
  }

  function toggleTelefoneTipo(container) {
    if (!container) return;
    var tipoSelect = container.querySelector('select[id$="-tipo"]');
    var telTipoWrapper = container.querySelector('.field-telefone_tipo');
    if (!tipoSelect || !telTipoWrapper) return;

    var isTelefone = (tipoSelect.value === 'telefone');
    telTipoWrapper.style.display = isTelefone ? '' : 'none';

    if (!isTelefone) {
      // Limpa radios/select quando não for telefone
      container.querySelectorAll('input[name$="-telefone_tipo"]:checked').forEach(function (el) {
        el.checked = false;
      });
      var select = container.querySelector('select[id$="-telefone_tipo"]');
      if (select) select.value = '';
    } else {
      // Default: ambos
      var hasChecked = container.querySelector('input[name$="-telefone_tipo"]:checked');
      if (!hasChecked) {
        var ambos = container.querySelector('input[name$="-telefone_tipo"][value="ambos"]');
        if (ambos) ambos.checked = true;
      }
      var select2 = container.querySelector('select[id$="-telefone_tipo"]');
      if (select2 && !select2.value) select2.value = 'ambos';
    }
  }

  function applyTelefoneMask(container) {
    if (!container) return;
    var tipoSelect = container.querySelector('select[id$="-tipo"]');
    var valorInput = container.querySelector('input[id$="-valor"]');
    if (!tipoSelect || !valorInput) return;

    // Evita adicionar listener repetido
    if (valorInput.dataset.phoneMaskBound === '1') return;
    valorInput.dataset.phoneMaskBound = '1';

    valorInput.addEventListener('input', function () {
      if (tipoSelect.value !== 'telefone') return;
      var start = valorInput.selectionStart;
      var before = valorInput.value;
      var formatted = formatPhoneBR(before);
      if (formatted !== before) {
        valorInput.value = formatted;
        try {
          // Mantém cursor no fim (simples e robusto)
          valorInput.setSelectionRange(valorInput.value.length, valorInput.value.length);
        } catch (e) {
          // ignore
        }
      } else if (start != null) {
        // no-op
      }
    });
  }

  function getInlineGroup() {
    // Django admin inlines (Stacked/Tabular) - prefix padrão: contatosite_set
    return (
      document.getElementById('contatosite_set-group') ||
      document.querySelector('.inline-group')
    );
  }

  function getInlineContainers(group) {
    if (!group) return [];
    // StackedInline usa .inline-related; TabularInline usa tr.form-row
    var stacked = Array.prototype.slice.call(group.querySelectorAll('.inline-related'));
    if (stacked.length) return stacked;
    return Array.prototype.slice.call(group.querySelectorAll('tbody tr.form-row'));
  }

  function addContato(tipo) {
    var group = getInlineGroup();
    if (!group) return;

    var addLink = group.querySelector('.add-row a');
    if (!addLink) return;

    addLink.click();

    // pega o último inline (stacked) ou linha (tabular)
    var containers = getInlineContainers(group);
    if (!containers.length) return;
    var container = containers[containers.length - 1];

    var tipoSelect = container.querySelector('select[id$="-tipo"]');
    if (tipoSelect) {
      tipoSelect.value = tipo;
      tipoSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    toggleTelefoneTipo(container);
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Inicial: esconde/mostra telefone_tipo conforme tipo
    var group = getInlineGroup();
    getInlineContainers(group).forEach(function (container) {
      toggleTelefoneTipo(container);
      applyTelefoneMask(container);
      var tipoSelect = container.querySelector('select[id$="-tipo"]');
      if (tipoSelect) {
        tipoSelect.addEventListener('change', function () {
          toggleTelefoneTipo(container);
        });
      }
    });

    // Botões "+" do change_form template
    document.querySelectorAll('[data-add-contato-tipo]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var tipo = btn.getAttribute('data-add-contato-tipo');
        addContato(tipo);
      });
    });

    // Quando adicionar nova linha via link padrão, re-aplica listeners
    if (group) {
      group.addEventListener('click', function (e) {
        var target = e.target;
        if (target && target.closest && target.closest('.add-row')) {
          setTimeout(function () {
            var containers = getInlineContainers(group);
            if (!containers.length) return;
            var container = containers[containers.length - 1];
            toggleTelefoneTipo(container);
            applyTelefoneMask(container);
            var tipoSelect = container.querySelector('select[id$="-tipo"]');
            if (tipoSelect) {
              tipoSelect.addEventListener('change', function () {
                toggleTelefoneTipo(container);
              });
            }
          }, 0);
        }
      });
    }
  });
})();
