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
    // IMPORTANTE:
    // Não use apenas dataset/data-attributes como flag de bind.
    // Em inlines do Django, o template "empty-form" (com __prefix__) é clonado.
    // Se marcarmos data-oc-money-bound="1" nele, o clone herda o atributo,
    // mas NÃO herda os event listeners — e o campo novo fica "marcado" sem máscara.
    if (!input || input.__ocMoneyBound) return;
    input.__ocMoneyBound = true;
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

    function normalizeCaretAfterClick() {
      // Em alguns casos o click coloca o cursor no decimal; forçamos pro inteiro.
      try {
        if ((input.dataset.ocMoneyMode || 'int') !== 'int') return;
        if (!String(input.value || '').trim()) return;
        ensureBase();
        var idx = String(input.value || '').indexOf(',');
        if (idx < 0) return;
        var pos = input.selectionStart;
        if (typeof pos === 'number' && pos > idx) {
          setCaretBeforeComma();
        }
      } catch (e) {
        // ignore
      }
    }

    input.addEventListener('mouseup', function () {
      setTimeout(normalizeCaretAfterClick, 0);
    });
    input.addEventListener('click', function () {
      setTimeout(normalizeCaretAfterClick, 0);
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

  function maskPercentIntOnBlur(input) {
    if (!input || input.dataset.ocPercentBound === '1') return;
    input.dataset.ocPercentBound = '1';

    try {
      if (input.type && input.type.toLowerCase() === 'number') {
        input.type = 'text';
      }
    } catch (e) {
      // ignore
    }

    function sanitize() {
      var digits = onlyDigits(input.value);
      var n = parseInt(digits || '0', 10);
      if (isNaN(n)) n = 0;
      if (n < 0) n = 0;
      if (n > 100) n = 100;
      input.value = String(n);
    }

    input.addEventListener('input', function () {
      // mantém o cursor mais estável: não força formatação a cada tecla
      input.value = onlyDigits(input.value).slice(0, 3);
    });

    input.addEventListener('blur', function () {
      sanitize();
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

  function getRealInlineContainers(group) {
    return getInlineContainers(group).filter(function (c) {
      return c && !(c.classList && c.classList.contains('empty-form'));
    });
  }

  function getLastRealContainer(group) {
    var containers = getRealInlineContainers(group);
    return containers.length ? containers[containers.length - 1] : null;
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
    getRealInlineContainers(group).forEach(function (container) {
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
      var last = getLastRealContainer(group);
      if (!last) return;
      bindContainer(last);

      var dailyEl = findInput(last, 'valor_diaria');
      maskMoneyOnBlur(dailyEl);
      computeAll();
    }, 50);
  }

  function bindNewInline(container) {
    if (!container || (container.classList && container.classList.contains('empty-form'))) return;
    bindContainer(container);
    var dailyEl = findInput(container, 'valor_diaria');
    maskMoneyOnBlur(dailyEl);
    computeAll();
  }

  function observeInlineAdds(group) {
    if (!group || group.dataset.ocObserverBound === '1') return;
    group.dataset.ocObserverBound = '1';

    try {
      var scheduled = false;
      var lastCount = 0;

      function scanAndBind() {
        scheduled = false;
        var containers = getInlineContainers(group).filter(function (c) {
          return c && !c.classList.contains('empty-form');
        });

        // Evita varredura sem necessidade
        if (containers.length === lastCount) return;
        lastCount = containers.length;

        containers.forEach(function (container) {
          bindContainer(container);
          var dailyEl = findInput(container, 'valor_diaria');
          maskMoneyOnBlur(dailyEl);
        });
        computeAll();
      }

      var mo = new MutationObserver(function (mutations) {
        var hasNewInline = false;

        for (var i = 0; i < mutations.length; i++) {
          var m = mutations[i];
          if (!m || !m.addedNodes || !m.addedNodes.length) continue;

          for (var j = 0; j < m.addedNodes.length; j++) {
            var n = m.addedNodes[j];
            if (!n || n.nodeType !== 1) continue;
            // Só reage quando realmente adicionou um inline/form novo
            if (
              (n.classList && n.classList.contains('inline-related')) ||
              (n.matches && n.matches('tr.form-row')) ||
              (n.querySelector && (n.querySelector('.inline-related') || n.querySelector('tr.form-row')))
            ) {
              hasNewInline = true;
              break;
            }
          }

          if (hasNewInline) break;
        }

        if (!hasNewInline) return;
        if (scheduled) return;
        scheduled = true;
        setTimeout(scanAndBind, 0);
      });

      mo.observe(group, { childList: true, subtree: true });
      // Inicializa contagem para não disparar à toa em alterações de texto
      lastCount = getInlineContainers(group).filter(function (c) {
        return c && !c.classList.contains('empty-form');
      }).length;
    } catch (e) {
      // ignore
    }
  }

  function bindChangelistUX() {
    var changelist = document.getElementById('changelist') || document.querySelector('.change-list');
    if (!changelist) return;

    function getCsrfToken() {
      // Preferência: token já renderizado no changelist-form do admin
      var el = document.querySelector('#changelist-form input[name="csrfmiddlewaretoken"]');
      if (el && el.value) return el.value;

      // Fallback: cookie padrão do Django
      try {
        var name = 'csrftoken';
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      } catch (e) {
        return null;
      }
    }

    function ensureDeleteModal() {
      var existing = document.getElementById('ocDeleteModal');
      if (existing) return existing;

      var overlay = document.createElement('div');
      overlay.id = 'ocDeleteModal';
      overlay.className = 'oc-modal';
      overlay.style.display = 'none';
      overlay.innerHTML =
        '<div class="oc-modal__backdrop" data-oc-close="1"></div>' +
        '<div class="oc-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="ocDeleteTitle">' +
        '  <div class="oc-modal__card card">' +
        '    <div class="card-body">' +
        '      <h5 id="ocDeleteTitle" class="card-title" style="font-weight:900;">Confirmar exclusão</h5>' +
        '      <p class="card-text" id="ocDeleteText" style="margin-bottom:14px;">Tem certeza que deseja excluir?</p>' +
        '      <div class="oc-modal__actions">' +
        '        <button type="button" class="btn btn-outline-secondary" data-oc-close="1">Cancelar</button>' +
        '        <button type="button" class="btn btn-danger" id="ocDeleteConfirm">Excluir</button>' +
        '      </div>' +
        '    </div>' +
        '  </div>' +
        '</div>';

      document.body.appendChild(overlay);
      return overlay;
    }

    function openDeleteModal(opts) {
      var modal = ensureDeleteModal();
      var text = modal.querySelector('#ocDeleteText');
      var btnConfirm = modal.querySelector('#ocDeleteConfirm');
      modal.__ocDeleteTarget = {
        url: (opts && opts.url) || null,
        id: (opts && opts.id) || null,
      };

      if (text) {
        text.textContent = modal.__ocDeleteTarget.id
          ? 'Excluir o orçamento #' + modal.__ocDeleteTarget.id + '?'
          : 'Tem certeza que deseja excluir este orçamento?';
      }

      function close() {
        modal.style.display = 'none';
        modal.classList.remove('oc-modal--open');
        if (btnConfirm) btnConfirm.disabled = false;
        document.removeEventListener('keydown', onKey);
      }

      function onKey(e) {
        if (e && e.key === 'Escape') close();
      }

      modal.querySelectorAll('[data-oc-close="1"]').forEach(function (el) {
        if (el.__ocBoundClose) return;
        el.__ocBoundClose = true;
        el.addEventListener('click', function () {
          close();
        });
      });

      if (btnConfirm && !btnConfirm.__ocBoundConfirm) {
        btnConfirm.__ocBoundConfirm = true;
        btnConfirm.addEventListener('click', function () {
          var target = modal.__ocDeleteTarget || {};
          if (!target.url) {
            close();
            return;
          }

          btnConfirm.disabled = true;

          // Submit real via form (mais confiável no Django Admin)
          var csrf = getCsrfToken();
          if (!csrf) {
            btnConfirm.disabled = false;
            close();
            window.location.href = target.url;
            return;
          }

          var form = document.createElement('form');
          form.method = 'POST';
          form.action = target.url;

          var inpCsrf = document.createElement('input');
          inpCsrf.type = 'hidden';
          inpCsrf.name = 'csrfmiddlewaretoken';
          inpCsrf.value = csrf;
          form.appendChild(inpCsrf);

          var inpPost = document.createElement('input');
          inpPost.type = 'hidden';
          inpPost.name = 'post';
          inpPost.value = 'yes';
          form.appendChild(inpPost);

          document.body.appendChild(form);
          form.submit();
        });
      }

      modal.style.display = 'block';
      modal.classList.add('oc-modal--open');
      document.addEventListener('keydown', onKey);
    }

    // Buscar enquanto digita
    var form = document.getElementById('changelist-search');
    var input = document.getElementById('searchbar');
    if (form && input) {
      // Identificação do campo (sem precisar do botão)
      if (!input.getAttribute('placeholder')) {
        input.setAttribute('placeholder', 'Pesquisar cliente...');
      }
      if (!input.getAttribute('aria-label')) {
        input.setAttribute('aria-label', 'Pesquisar cliente');
      }

      var t = null;
      var last = String(input.value || '');
      input.addEventListener('input', function () {
        var v = String(input.value || '');
        if (v === last) return;
        last = v;
        if (t) window.clearTimeout(t);
        t = window.setTimeout(function () {
          form.submit();
        }, 250);
      });
    }

    // Ações só quando selecionar
    var actions = document.querySelector('#changelist-form .actions');
    function updateActionsVisibility() {
      if (!actions) return;
      var any = !!document.querySelector('#changelist-form input.action-select:checked');
      actions.style.display = any ? '' : 'none';
    }
    if (actions) {
      updateActionsVisibility();
      document.addEventListener('change', function (e) {
        var target = e.target;
        if (!target) return;
        if (target.matches && (target.matches('#action-toggle') || target.matches('input.action-select'))) {
          updateActionsVisibility();
        }
      });
    }

    // Confirmação na lixeira por linha
    // Delegado (mais confiável no mobile e cobre linhas geradas dinamicamente)
    if (!changelist.__ocDeleteDelegated) {
      changelist.__ocDeleteDelegated = true;
      changelist.addEventListener(
        'click',
        function (e) {
          var target = e && e.target;
          if (!target || !target.closest) return;
          var a = target.closest('a.oc-row-delete[data-oc-delete="1"]');
          if (!a) return;
          e.preventDefault();
          e.stopPropagation();
          openDeleteModal({ url: a.getAttribute('href'), id: a.getAttribute('data-oc-id') });
        },
        true
      );
    }

    // Linha inteira clicável: abre o orçamento ao clicar em qualquer lugar da linha.
    var resultList = document.getElementById('result_list');
    if (resultList) {
      resultList.querySelectorAll('tbody tr').forEach(function (tr) {
        if (tr.__ocRowBound) return;
        tr.__ocRowBound = true;

        tr.addEventListener('click', function (e) {
          var target = e && e.target;
          if (!target) return;

          // Não dispara ao clicar em checkbox, links, botões ou na lixeira.
          if (
            (target.closest && target.closest('a')) ||
            (target.closest && target.closest('button')) ||
            (target.closest && target.closest('input'))
          ) {
            return;
          }

          var link = tr.querySelector('th a, td a');
          if (link && link.getAttribute) {
            var href = link.getAttribute('href');
            if (href) window.location.href = href;
          }
        });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindChangelistUX();

    // Fallback: se algum inline novo escapar dos binds, aplica máscara ao focar.
    document.addEventListener(
      'focusin',
      function (e) {
        var target = e && e.target;
        if (!target || !target.matches) return;
        if (target.matches('input[id$="-valor_diaria"]')) {
          maskMoneyOnBlur(target);
          return;
        }
        if (target.matches('input[name="desconto_valor"]')) {
          maskMoneyOnBlur(target);
          return;
        }
        if (target.matches('input[name="desconto_percentual"]')) {
          maskPercentIntOnBlur(target);
        }
      },
      true
    );

    // Move os campos de desconto para o final (abaixo dos itens).
    var mount = document.getElementById('ocDescontoArea');
    if (mount) {
      var descontoValorRow = document.querySelector('.form-row.field-desconto_valor, .form-group.field-desconto_valor');
      var descontoPctRow = document.querySelector('.form-row.field-desconto_percentual, .form-group.field-desconto_percentual');
      if (descontoValorRow) mount.appendChild(descontoValorRow);
      if (descontoPctRow) mount.appendChild(descontoPctRow);
    }

    // Botão aplicar desconto (R$ ou %) — renderizado no template
    var applyBtn = document.querySelector('.oc-apply-discount-btn');
    if (applyBtn && !applyBtn.__ocBound) {
      applyBtn.__ocBound = true;
      applyBtn.addEventListener('click', function () {
        var dv = findMainInputByName('desconto_valor');
        var dp = findMainInputByName('desconto_percentual');
        var v = toFloatBR(dv && dv.value);
        var p = toFloatBR(dp && dp.value);

        // Escolhe um só: se % > 0, zera R$; senão mantém R$
        if (p > 0) {
          if (dv) dv.value = '0,00';
        } else if (v > 0) {
          if (dp) dp.value = '0';
        }
        computeAll();
      });
    }

    // Máscara da data do evento (dd/mm/aaaa)
    maskDateDDMMYYYY(findMainInputByName('data_evento'));

    // Máscara do desconto
    maskMoneyOnBlur(findMainInputByName('desconto_valor'));
    maskPercentIntOnBlur(findMainInputByName('desconto_percentual'));

    var group = getInlineGroup();
    getRealInlineContainers(group).forEach(function (container) {
      bindContainer(container);
    });

    // Máscara do valor da diária apenas nos inlines reais (não no template empty-form/__prefix__)
    if (group) {
      getRealInlineContainers(group).forEach(function (container) {
        var dailyEl = findInput(container, 'valor_diaria');
        maskMoneyOnBlur(dailyEl);
      });
    }

    observeInlineAdds(group);

    // Django admin dispara este evento ao adicionar inline (mais confiável que observer)
    try {
      if (window.django && window.django.jQuery) {
        window.django.jQuery(document).on('formset:added', function (_event, row) {
          // row pode vir como elemento DOM ou como jQuery object
          var el = row;
          if (el && el.jquery) {
            el = el[0];
          }
          bindNewInline(el);
        });
      }
    } catch (e) {
      // ignore
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
            var last = getLastRealContainer(group);
            if (!last) return;
            bindNewInline(last);
          }, 50);
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
