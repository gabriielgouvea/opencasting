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

  function formatNumberBR(num) {
    try {
      return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num || 0);
    } catch (e) {
      var n = (num || 0).toFixed(2);
      return String(n).replace('.', ',');
    }
  }

  function formatIntBR(intValue) {
    try {
      return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(intValue || 0);
    } catch (e) {
      return String(intValue || 0);
    }
  }

  function maskMoneyOnBlur(input) {
    if (!input || input.dataset.ocMoneyBound === '1') return;
    input.dataset.ocMoneyBound = '1';

    // Garante que o campo aceite vírgula (se alguém renderizar como type=number)
    try {
      if (input.type && input.type.toLowerCase() === 'number') {
        input.type = 'text';
      }
    } catch (e) {
      // ignore
    }

    function ensureBase() {
      var raw = String(input.value || '').trim();
      if (!raw) {
        input.value = '0,00';
      } else if (raw.indexOf(',') < 0) {
        // Se vier só número, garante ,00
        var digits = onlyDigits(raw);
        var nInt = parseInt(digits || '0', 10);
        if (isNaN(nInt)) nInt = 0;
        input.value = formatIntBR(nInt) + ',00';
      } else {
        // Ajusta para sempre ter 2 casas
        var parts = raw.split(',');
        var intDigits = onlyDigits(parts[0]);
        var decDigits = onlyDigits(parts.slice(1).join(',')).slice(0, 2);
        var intNum = parseInt(intDigits || '0', 10);
        if (isNaN(intNum)) intNum = 0;
        input.value = formatIntBR(intNum) + ',' + (decDigits + '00').slice(0, 2);
      }
    }

    function setCaretBeforeComma() {
      try {
        var idx = String(input.value || '').indexOf(',');
        if (idx < 0) idx = String(input.value || '').length;
        input.setSelectionRange(idx, idx);
      } catch (e) {
        // ignore
      }
    }

    function setCaretAfterComma(pos) {
      try {
        var idx = String(input.value || '').indexOf(',');
        if (idx < 0) idx = 0;
        var p = idx + 1 + (pos || 0);
        input.setSelectionRange(p, p);
      } catch (e) {
        // ignore
      }
    }

    function parseParts() {
      ensureBase();
      var raw = String(input.value || '0,00');
      var parts = raw.split(',');
      var intDigits = onlyDigits(parts[0]) || '0';
      var decDigits = onlyDigits(parts[1] || '').slice(0, 2);
      decDigits = (decDigits + '00').slice(0, 2);
      return { intDigits: intDigits, decDigits: decDigits };
    }

    function renderParts(intDigits, decDigits) {
      var intNum = parseInt(intDigits || '0', 10);
      if (isNaN(intNum)) intNum = 0;
      input.value = formatIntBR(intNum) + ',' + (String(decDigits || '') + '00').slice(0, 2);
    }

    // Controle de modo de edição
    input.dataset.ocMoneyMode = input.dataset.ocMoneyMode || 'int';
    input.dataset.ocMoneyDecPos = input.dataset.ocMoneyDecPos || '0';

    input.addEventListener('focus', function () {
      // Não força valor quando o usuário só clicou; mas se já tiver algo, alinha cursor no inteiro.
      if (String(input.value || '').trim()) {
        ensureBase();
        input.dataset.ocMoneyMode = 'int';
        input.dataset.ocMoneyDecPos = '0';
        setCaretBeforeComma();
      }
    });

    input.addEventListener('keydown', function (e) {
      var key = e.key;
      if (!key) return;

      // Atalhos/teclas de navegação
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (key === 'Tab' || key === 'ArrowLeft' || key === 'ArrowRight' || key === 'Home' || key === 'End') return;

      // Vírgula: entra no modo decimal
      if (key === ',') {
        e.preventDefault();
        ensureBase();
        input.dataset.ocMoneyMode = 'dec';
        input.dataset.ocMoneyDecPos = '0';
        setCaretAfterComma(0);
        return;
      }

      // Números
      if (/^\d$/.test(key)) {
        e.preventDefault();
        var parts = parseParts();
        var mode = input.dataset.ocMoneyMode || 'int';

        if (mode === 'dec') {
          var pos = parseInt(input.dataset.ocMoneyDecPos || '0', 10);
          if (isNaN(pos) || pos < 0) pos = 0;
          if (pos > 1) pos = 1;
          var d = parts.decDigits.split('');
          d[pos] = key;
          parts.decDigits = d.join('');
          renderParts(parts.intDigits, parts.decDigits);
          pos = Math.min(pos + 1, 2);
          input.dataset.ocMoneyDecPos = String(pos);
          setCaretAfterComma(pos);
          return;
        }

        // modo inteiro: sempre adiciona no final
        var intDigits = parts.intDigits;
        if (intDigits === '0') {
          intDigits = key;
        } else {
          intDigits = intDigits + key;
        }
        renderParts(intDigits, parts.decDigits);
        input.dataset.ocMoneyMode = 'int';
        input.dataset.ocMoneyDecPos = '0';
        setCaretBeforeComma();
        return;
      }

      // Backspace
      if (key === 'Backspace') {
        e.preventDefault();
        var partsB = parseParts();
        var modeB = input.dataset.ocMoneyMode || 'int';

        if (modeB === 'dec') {
          var posB = parseInt(input.dataset.ocMoneyDecPos || '0', 10);
          if (isNaN(posB) || posB < 0) posB = 0;
          if (posB > 2) posB = 2;
          if (posB > 0) {
            posB -= 1;
            var db = partsB.decDigits.split('');
            db[posB] = '0';
            partsB.decDigits = db.join('');
            renderParts(partsB.intDigits, partsB.decDigits);
            input.dataset.ocMoneyDecPos = String(posB);
            setCaretAfterComma(posB);
            return;
          }
          // se estiver no decimal e pos=0, volta pro inteiro
          input.dataset.ocMoneyMode = 'int';
          setCaretBeforeComma();
          return;
        }

        // modo inteiro: remove último dígito
        var id = partsB.intDigits || '0';
        if (id.length <= 1) {
          id = '0';
        } else {
          id = id.slice(0, -1);
        }
        renderParts(id, partsB.decDigits);
        input.dataset.ocMoneyMode = 'int';
        input.dataset.ocMoneyDecPos = '0';
        setCaretBeforeComma();
        return;
      }

      // Delete: ignora (deixa browser)
      if (key === 'Delete') return;

      // Bloqueia qualquer outro caractere
      if (key.length === 1) {
        e.preventDefault();
      }
    });

    input.addEventListener('blur', function () {
      var raw = String(input.value || '').trim();
      if (!raw) return;
      var n = toFloatBR(raw);
      input.value = formatNumberBR(n);
      input.dataset.ocMoneyMode = 'int';
      input.dataset.ocMoneyDecPos = '0';
    });
  }

  function maskDateDDMMYYYY(input) {
    if (!input || input.dataset.ocDateBound === '1') return;
    input.dataset.ocDateBound = '1';

    // Se vier como date, força text para permitir digitar números
    try {
      if (input.type && input.type.toLowerCase() === 'date') {
        input.type = 'text';
      }
    } catch (e) {
      // ignore
    }

    input.addEventListener('input', function () {
      var d = onlyDigits(input.value).slice(0, 8);
      if (!d) {
        input.value = '';
        return;
      }
      if (d.length <= 2) {
        input.value = d;
        return;
      }
      if (d.length <= 4) {
        input.value = d.slice(0, 2) + '/' + d.slice(2);
        return;
      }
      input.value = d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    });
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

  function findMainInputByName(name) {
    return document.querySelector('input[name="' + name + '"]');
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
    var subtotal = 0;
    getInlineContainers(group).forEach(function (container) {
      // ignora forms vazios que o Django usa como template
      if (container.classList.contains('empty-form')) return;
      subtotal += computeLine(container);
    });

    var descontoValorEl = findMainInputByName('desconto_valor');
    var descontoPctEl = findMainInputByName('desconto_percentual');
    var descontoValor = toFloatBR(descontoValorEl && descontoValorEl.value);
    var descontoPct = toFloatBR(descontoPctEl && descontoPctEl.value);

    var descontoAplicado = 0;
    if (descontoPct > 0) {
      if (descontoPct > 100) descontoPct = 100;
      descontoAplicado = (subtotal * descontoPct) / 100;
    } else if (descontoValor > 0) {
      descontoAplicado = descontoValor;
    }

    if (descontoAplicado < 0) descontoAplicado = 0;
    if (descontoAplicado > subtotal) descontoAplicado = subtotal;

    var totalFinal = subtotal - descontoAplicado;

    var totalEl = document.getElementById('ocOrcamentoTotal');
    if (totalEl) totalEl.textContent = formatBRL(totalFinal);

    var hintEl = document.getElementById('ocOrcamentoHint');
    if (hintEl) {
      if (descontoAplicado > 0) {
        hintEl.textContent = 'Subtotal: ' + formatBRL(subtotal) + '  |  Desconto: -' + formatBRL(descontoAplicado);
      } else {
        hintEl.textContent = '';
      }
    }
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
    // Move os campos de desconto para o final (abaixo dos itens).
    var mount = document.getElementById('ocDescontoArea');
    if (mount) {
      var descontoValorRow = document.querySelector('.form-row.field-desconto_valor, .form-group.field-desconto_valor');
      var descontoPctRow = document.querySelector('.form-row.field-desconto_percentual, .form-group.field-desconto_percentual');
      if (descontoValorRow) mount.appendChild(descontoValorRow);
      if (descontoPctRow) mount.appendChild(descontoPctRow);
    }

    // Máscara da data do evento (dd/mm/aaaa)
    maskDateDDMMYYYY(findMainInputByName('data_evento'));

    // Máscara do desconto
    maskMoneyOnBlur(findMainInputByName('desconto_valor'));
    maskMoneyOnBlur(findMainInputByName('desconto_percentual'));

    var group = getInlineGroup();
    getInlineContainers(group).forEach(function (container) {
      bindContainer(container);
    });

    // Máscara do valor da diária em todos os inlines
    if (group) {
      Array.prototype.slice
        .call(group.querySelectorAll('input[id$="-valor_diaria"]'))
        .forEach(function (el) {
          maskMoneyOnBlur(el);
        });
    }

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

            var dailyEl = findInput(last, 'valor_diaria');
            maskMoneyOnBlur(dailyEl);

            computeAll();
          }, 0);
        }
      });
    }

    // Recalcula quando o desconto muda
    var dv = findMainInputByName('desconto_valor');
    var dp = findMainInputByName('desconto_percentual');
    if (dv) {
      dv.addEventListener('input', computeAll);
      dv.addEventListener('change', computeAll);
    }
    if (dp) {
      dp.addEventListener('input', computeAll);
      dp.addEventListener('change', computeAll);
    }

    computeAll();
  });
})();
