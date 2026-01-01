(function () {
  function onlyDigits(value) {
    return String(value || '').replace(/\D+/g, '');
  }

  function toFloatBR(value) {
    var s = String(value || '').trim();
    if (!s) return 0;
    // aceita "400" "400,50" "400.50" "R$ 400,50"
    s = s.replace(/[^0-9.,-]/g, '');
    // se tiver vírgula, assume formato BR
    if (s.indexOf(',') >= 0) {
      s = s.replace(/\./g, '').replace(',', '.');
    }
    var n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  function formatBRL(num) {
    try {
      return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(num || 0);
    } catch (e) {
      var n = (num || 0).toFixed(2);
      return 'R$ ' + n.replace('.', ',');
    }
  }

  function getInlineGroup() {
    return (
      document.getElementById('itens-group') ||
      document.getElementById('orcamentoitem_set-group') ||
      document.querySelector('.inline-group')
    );
  }

  function getInlineContainers(group) {
    if (!group) return [];
    var stacked = Array.prototype.slice.call(group.querySelectorAll('.inline-related'));
    if (stacked.length) return stacked;
    return Array.prototype.slice.call(group.querySelectorAll('tbody tr.form-row'));
  }

  function findInput(container, suffix) {
    if (!container) return null;
    return container.querySelector('input[id$="-' + suffix + '"], select[id$="-' + suffix + '"]');
  }

  function ensureLineTotalEl(container) {
    var existing = container.querySelector('[data-oc-line-total]');
    if (existing) return existing;

    var wrap = document.createElement('div');
    wrap.setAttribute('data-oc-line-total', '1');
    wrap.className = 'oc-line-total';
    wrap.innerHTML = '<div class="oc-line-total-label">Total da função</div><div class="oc-line-total-value">R$ 0,00</div>';

    var target = container.querySelector('.form-row:last-child') || container;
    target.appendChild(wrap);
    return wrap;
  }

  function computeLine(container) {
    var qtyEl = findInput(container, 'quantidade');
    var daysEl = findInput(container, 'diarias');
    var dailyEl = findInput(container, 'valor_diaria');

    var qty = parseInt(onlyDigits(qtyEl && qtyEl.value), 10);
    var days = parseInt(onlyDigits(daysEl && daysEl.value), 10);
    var daily = toFloatBR(dailyEl && dailyEl.value);

    if (isNaN(qty)) qty = 0;
    if (isNaN(days)) days = 0;

    var total = qty * days * daily;

    var el = ensureLineTotalEl(container);
    var valueEl = el.querySelector('.oc-line-total-value');
    if (valueEl) valueEl.textContent = formatBRL(total);

    return total;
  }

  function computeAll() {
    var group = getInlineGroup();
    var total = 0;
    getInlineContainers(group).forEach(function (container) {
      // ignora forms vazios que o Django usa como template
      if (container.classList.contains('empty-form')) return;
      total += computeLine(container);
    });

    var totalEl = document.getElementById('ocOrcamentoTotal');
    if (totalEl) totalEl.textContent = formatBRL(total);
  }

  function bindContainer(container) {
    if (!container || container.dataset.ocBound === '1') return;
    container.dataset.ocBound = '1';

    ['funcao', 'quantidade', 'carga_horaria_horas', 'valor_diaria', 'diarias'].forEach(function (suffix) {
      var el = findInput(container, suffix);
      if (!el) return;
      el.addEventListener('input', computeAll);
      el.addEventListener('change', computeAll);
    });

    computeLine(container);
  }

  function addFuncao() {
    var group = getInlineGroup();
    if (!group) return;
    var addLink = group.querySelector('.add-row a');
    if (!addLink) return;
    addLink.click();

    setTimeout(function () {
      var containers = getInlineContainers(group);
      if (!containers.length) return;
      var last = containers[containers.length - 1];
      bindContainer(last);
      computeAll();
    }, 0);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var group = getInlineGroup();
    getInlineContainers(group).forEach(function (container) {
      bindContainer(container);
    });

    document.querySelectorAll('[data-add-orcamento-item]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        addFuncao();
      });
    });

    if (group) {
      group.addEventListener('click', function (e) {
        var target = e.target;
        if (target && target.closest && target.closest('.add-row')) {
          setTimeout(function () {
            var containers = getInlineContainers(group);
            if (!containers.length) return;
            var last = containers[containers.length - 1];
            bindContainer(last);
            computeAll();
          }, 0);
        }
      });
    }

    computeAll();
  });
})();
