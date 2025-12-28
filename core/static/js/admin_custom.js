/**
 * OPENCASTING CRM - GESTOR V16 (JAZZMIN BOOTSTRAP SUPPORT)
 * ------------------------------------------------------------------
 * 1. SUPORTE JAZZMIN: Lê filtros dentro de Cards/Bootstraps.
 * 2. VISIBILIDADE: Garante que os filtros sejam encontrados.
 * 3. FERRAMENTAS: WhatsApp, Links e Ações em Massa.
 */

(function() {
    'use strict';

    // Evita carregar/executar duas vezes (Jazzmin às vezes injeta assets duplicados)
    if (window.__opencasting_admin_custom_loaded) {
        return;
    }
    window.__opencasting_admin_custom_loaded = true;

    const CHECK_INTERVAL = 500;
    let isSidebarBuilt = false;
    let searchDebounceTimer = null;
    let liveSearchAbortController = null;
    let liveSearchLastApplied = null;

    // Garante SweetAlert2
    if (typeof Swal === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
        document.head.appendChild(script);
    }

    // --- FUNÇÕES GLOBAIS ---
    window.openCastingFilters = function() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        const backdrop = document.getElementById('filter-backdrop');
        if (sidebar && backdrop) {
            sidebar.classList.add('active');
            backdrop.style.display = 'block';
            try { fixSelectWidgetsInSidebar(); } catch(e) {}
            // Auto-aplicar: garante handlers ao abrir
            try { bindSidebarFilterAutoApply(); } catch(e) {}
        } else {
            buildFilterSidebar();
            setTimeout(() => window.openCastingFilters(), 200);
        }
    };

    window.closeSidebar = function() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        const backdrop = document.getElementById('filter-backdrop');
        if(sidebar) sidebar.classList.remove('active');
        if(backdrop) backdrop.style.display = 'none';
    };

    function setKeepSidebarOpen(flag) {
        try {
            if (flag) sessionStorage.setItem('__oc_keep_sidebar_open', '1');
            else sessionStorage.removeItem('__oc_keep_sidebar_open');
        } catch (e) {}
    }

    function shouldKeepSidebarOpen() {
        try {
            return sessionStorage.getItem('__oc_keep_sidebar_open') === '1';
        } catch (e) {
            return false;
        }
    }

    function findSidebarSearchSubmitButton() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        if (!sidebar) return null;
        // tenta achar um botão/submit com texto "pesquisar" dentro da sidebar
        const candidates = Array.from(sidebar.querySelectorAll('button, input[type="submit"], input[type="button"], a[role="button"]'));
        for (const el of candidates) {
            const txt = ((el.innerText || el.value || '') + '').toLowerCase().trim();
            if (txt.includes('pesquisar') || txt.includes('buscar')) return el;
        }
        return null;
    }

    function submitChangelistForm() {
        const form = document.getElementById('changelist-form');
        if (!form) return;
        try { form.submit(); } catch (e) {}
    }

    function triggerAutoApplyFromSidebar() {
        // Após selecionar um filtro, aplica (submete) e reabre sidebar após reload
        setKeepSidebarOpen(true);
        const btn = findSidebarSearchSubmitButton();
        if (btn) {
            try {
                // Alguns temas usam botão type=button; outros submit.
                btn.click();
                return;
            } catch (e) {}
        }
        submitChangelistForm();
    }

    // Ao mudar qualquer select de filtro dentro da sidebar, aplica imediatamente.
    // Mantém a sidebar aberta (reabre após reload).
    function bindSidebarFilterAutoApply() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        if (!sidebar) return;
        if (sidebar.dataset.boundAutoApply === '1') return;
        sidebar.dataset.boundAutoApply = '1';

        const content = sidebar.querySelector('#sidebar-content') || sidebar;

        // 1) Selects (inclui Select2, pois ele dispara 'change' no select original)
        content.querySelectorAll('select').forEach(sel => {
            if (!sel.name) return;
            // não interferir no select de ações
            if (sel.name === 'action') return;
            // não auto-aplicar quando o user só abre o dropdown

            if (sel.dataset.ocBoundChange === '1') return;
            sel.dataset.ocBoundChange = '1';

            sel.addEventListener('change', () => {
                // Se o usuário está no status (abas), deixamos seguir comportamento normal
                // (mas na prática status é tratado pelos tabs e pelo select de status)
                triggerAutoApplyFromSidebar();
            });
        });

        // 2) Links de filtros copiados (H3 + UL), se existirem
        content.querySelectorAll('#django-filters-target a').forEach(a => {
            if (a.dataset.ocBoundLink === '1') return;
            a.dataset.ocBoundLink = '1';
            a.addEventListener('click', (ev) => {
                const href = a.getAttribute('href');
                if (!href) return;
                ev.preventDefault();
                setKeepSidebarOpen(true);
                window.location.href = href;
            });
        });

        // 3) Botão Pesquisar: ao clicar, fecha a sidebar (não reabre)
        const searchBtn = findSidebarSearchSubmitButton();
        if (searchBtn && searchBtn.dataset.ocBoundClose !== '1') {
            searchBtn.dataset.ocBoundClose = '1';
            searchBtn.addEventListener('click', () => {
                setKeepSidebarOpen(false);
                try { window.closeSidebar(); } catch (e) {}
            });
        }

        // 4) Botão voltar (setinha): fecha a sidebar (mantém filtros já aplicados)
        const backBtn = document.getElementById('btn-back-sidebar');
        if (backBtn && backBtn.dataset.ocBound !== '1') {
            backBtn.dataset.ocBound = '1';
            backBtn.addEventListener('click', () => {
                setKeepSidebarOpen(false);
                window.closeSidebar();
            });
        }
    }

    function ensureNoResultsMessage() {
        // Evita "tela branca" quando nenhum registro combina com os filtros.
        try {
            if (!window.location.pathname.includes('/admin/core/userprofile/')) return;

            const results = document.querySelector('#changelist-form .results') || document.querySelector('.results');
            if (!results) return;

            // remove mensagem antiga se existir
            results.querySelectorAll('.oc-no-results').forEach(n => n.remove());

            const table = document.getElementById('result_list');
            let hasRows = false;
            if (table) {
                const bodyRows = table.querySelectorAll('tbody tr');
                hasRows = bodyRows && bodyRows.length > 0;
            }

            // Alguns templates podem omitir a tabela quando vazio
            if (!table) {
                const anyRow = results.querySelector('tbody tr, table tr');
                hasRows = !!anyRow;
            }

            if (!hasRows) {
                const box = document.createElement('div');
                box.className = 'oc-no-results';
                box.innerHTML = '<div class="oc-no-results-title">Nenhum promotor encontrado</div><div class="oc-no-results-sub">Tente ajustar ou limpar os filtros.</div>';
                results.prepend(box);
            }
        } catch (e) {}
    }

    // Proteção: alguns temas removem/alteram markup e o actions.js do Django quebra.
    // Criamos um .action-counter “inofensivo” se não existir.
    function ensureDjangoActionsCounter() {
        // Tenta encontrar qualquer contador existente
        let counter = document.querySelector('.action-counter');
        
        // Se não existir, cria um
        if (!counter) {
            const actions = document.querySelector('.actions') || document.getElementById('changelist-form') || document.body;
            counter = document.createElement('span');
            counter.className = 'action-counter';
            counter.style.display = 'none';
            actions.prepend(counter);
        }
        
        // Garante que tenha o atributo dataset necessário para o actions.js não quebrar
        if (!counter.dataset.actionsIcnt) {
            counter.dataset.actionsIcnt = '0';
        }
    }

    // Select2/Bootstrap selects podem “sumir” quando movidos para um container com z-index alto.
    // Aqui reinicializamos os selects já-controlados por Select2 para usar a sidebar como dropdownParent.
    function fixSelectWidgetsInSidebar() {
        const sidebarEl = document.getElementById('custom-sidebar-filter');
        if (!sidebarEl) return;

        const $ = (window.django && window.django.jQuery) ? window.django.jQuery : null;
        if (!$ || !$.fn) return;
        if (!$.fn.select2) return;

        const $sidebar = $(sidebarEl);
        $sidebar.find('select').each(function() {
            const $sel = $(this);

            // Só mexe nos selects que JÁ eram Select2 (evita transformar selects nativos)
            const isSelect2 = $sel.hasClass('select2-hidden-accessible') || !!$sel.data('select2') || $sel.is('[data-select2-id]');
            if (!isSelect2) return;

            try {
                $sel.select2('destroy');
            } catch (e) {}

            try {
                $sel.select2({
                    width: '100%',
                    dropdownParent: $sidebar
                });
            } catch (e) {}
        });
    }

    // --- SIDEBAR BUILDER ---
    function normalizeText(s) {
        try {
            return (s || '')
                .toString()
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .trim();
        } catch (e) {
            return (s || '').toString().toLowerCase().trim();
        }
    }

    // Multi-seleção de Área de Atuação (checkbox + aplicar/limpar)
    function enhanceAreasAtuacaoMultiSelect() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        if (!sidebar) return;

        const currentRaw = (new URLSearchParams(window.location.search || '').get('area_atuacao') || '').trim();
        const currentSet = new Set(
            currentRaw
                .split(/[,;|]+/)
                .map(v => (v || '').trim())
                .filter(Boolean)
        );

        function buildWidget(items, mountEl, opts) {
            if (!mountEl) return;
            if (mountEl.dataset && mountEl.dataset.ocEnhanced === '1') return;
            if (!items || items.length === 0) return;

            const wrap = document.createElement('div');
            wrap.className = 'oc-area-multi';
            wrap.style.marginBottom = '12px';

            const list = document.createElement('div');
            list.className = 'oc-area-multi-list';

            items.forEach((it, idx) => {
                const id = `oc-area-${idx}-${Math.random().toString(16).slice(2)}`;
                const row = document.createElement('label');
                row.setAttribute('for', id);
                row.style.display = 'flex';
                row.style.alignItems = 'center';
                row.style.gap = '8px';
                row.style.margin = '0 0 6px 0';
                row.style.fontSize = '0.85rem';
                row.style.color = '#666';

                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.id = id;
                cb.value = it.value;
                cb.checked = currentSet.has(it.value);
                cb.style.transform = 'translateY(-1px)';

                const span = document.createElement('span');
                span.innerText = it.label;

                row.appendChild(cb);
                row.appendChild(span);
                list.appendChild(row);
            });

            const actions = document.createElement('div');
            actions.style.display = 'flex';
            actions.style.gap = '8px';
            actions.style.marginTop = '8px';

            const btnApply = document.createElement('button');
            btnApply.type = 'button';
            btnApply.className = 'btn btn-sm btn-primary';
            btnApply.innerText = 'Aplicar';

            const btnClear = document.createElement('button');
            btnClear.type = 'button';
            btnClear.className = 'btn btn-sm btn-light';
            btnClear.innerText = 'Limpar';

            function navigateWithSelection(selectedValues) {
                const url = new URL(window.location.href);
                if (selectedValues.length > 0) {
                    url.searchParams.set('area_atuacao', selectedValues.join(','));
                } else {
                    url.searchParams.delete('area_atuacao');
                }
                url.searchParams.delete('p');
                window.location.href = url.toString();
            }

            btnApply.addEventListener('click', () => {
                const selected = Array.from(list.querySelectorAll('input[type="checkbox"]:checked'))
                    .map(i => (i.value || '').trim())
                    .filter(Boolean);
                navigateWithSelection(selected);
            });

            btnClear.addEventListener('click', () => {
                list.querySelectorAll('input[type="checkbox"]').forEach(i => { i.checked = false; });
                navigateWithSelection([]);
            });

            actions.appendChild(btnApply);
            actions.appendChild(btnClear);

            wrap.appendChild(list);
            wrap.appendChild(actions);

            mountEl.dataset.ocEnhanced = '1';
            if (opts && opts.replace) {
                mountEl.replaceWith(wrap);
            } else {
                mountEl.insertAdjacentElement('afterend', wrap);
            }
        }

        // Caso 1: filtros do Django clonados (H3 + UL)
        const root = document.getElementById('django-filters-target');
        if (root) {
            const headers = Array.from(root.querySelectorAll('h3'));
            const header = headers.find(h => normalizeText(h.innerText).includes('area de atuacao'));
            if (header) {
                let ul = header.nextElementSibling;
                while (ul && ul.tagName !== 'UL') ul = ul.nextElementSibling;
                if (ul) {
                    const items = Array.from(ul.querySelectorAll('li a'))
                        .map(a => {
                            const href = a.getAttribute('href') || '';
                            const label = (a.innerText || '').trim();
                            let value = '';
                            try {
                                const u = new URL(href, window.location.origin);
                                value = (u.searchParams.get('area_atuacao') || '').trim();
                            } catch (e) {
                                const m = href.match(/[?&]area_atuacao=([^&]+)/i);
                                value = m ? decodeURIComponent(m[1] || '') : '';
                            }
                            return { label, value };
                        })
                        .filter(it => !!it.value);

                    if (items.length > 0) {
                        buildWidget(items, ul, { replace: true });
                        return;
                    }
                }
            }
        }

        // Caso 2: filtro renderizado como SELECT (ex: painel movido / tema)
        const select = sidebar.querySelector('select[name="area_atuacao"], select#id_area_atuacao');
        if (select) {
            if (select.dataset && select.dataset.ocEnhanced === '1') return;

            const items = Array.from(select.options || [])
                .map(o => ({ value: (o.value || '').trim(), label: (o.text || '').trim() }))
                .filter(it => !!it.value && it.value !== '---------');

            if (items.length === 0) return;

            // Esconde o select e também o container do Select2 (se existir)
            try { select.style.setProperty('display', 'none', 'important'); } catch(e) { select.style.display = 'none'; }
            try {
                const next = select.nextElementSibling;
                if (next && next.classList && (next.classList.contains('select2') || next.classList.contains('select2-container'))) {
                    next.style.setProperty('display', 'none', 'important');
                }
            } catch (e) {}
            buildWidget(items, select, { replace: false });
        }
    }

    // Converte selects de filtros na SIDEBAR em um dropdown com checkboxes (multi-seleção).
    // Visual: mantém o padrão "campo com setinha"; ao abrir, lista com checks.
    // Gera query params no formato <campo>__in=val1,val2.
    // Importante: não converte o status (abas) para não quebrar a navegação padrão.
    function enhanceSidebarMultiCheckboxFilters() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        if (!sidebar) return;

        const sidebarContent = sidebar.querySelector('#sidebar-content') || sidebar;

        // Evita duplicar UI global
        try {
            sidebar.querySelectorAll('.oc-multi-filters').forEach(el => el.remove());
        } catch (e) {}

        const selects = Array.from(sidebarContent.querySelectorAll('select'))
            .filter(s => s && s.name && s.name !== 'action')
            .filter(s => !(s.closest && s.closest('.select2-container')));

        if (selects.length === 0) return;

        function prettifyLabelFromName(name) {
            const base = (name || '').replace(/__exact$/i, '').replace(/__id__exact$/i, '');
            const cleaned = base.replace(/_/g, ' ').trim();
            return cleaned ? (cleaned.charAt(0).toUpperCase() + cleaned.slice(1)) : 'Filtro';
        }

        function computeInParam(selectName) {
            if (!selectName) return null;
            if (selectName === 'area_atuacao') return 'area_atuacao';
            // padrão do Django admin para choices: <field>__exact
            if (selectName.endsWith('__exact')) {
                return selectName.replace(/__exact$/i, '__in');
            }
            return selectName + '__in';
        }

        function splitMulti(raw) {
            return (raw || '')
                .toString()
                .split(/[,;|]+/)
                .map(v => (v || '').trim())
                .filter(Boolean);
        }

        const urlParams = new URLSearchParams(window.location.search || '');

        // Container novo de UI
        const ui = document.createElement('div');
        ui.className = 'oc-multi-filters';

        const groups = [];

        selects.forEach(sel => {
            const name = (sel.name || '').trim();
            if (!name) return;

            // não quebrar abas de status
            if (name === 'status__exact' || name === 'status') return;
            // Área de atuação já tem widget próprio
            if (name === 'area_atuacao') return;

            // Evita converter duas vezes o mesmo select
            if (sel.dataset && sel.dataset.ocMultiConverted === '1') return;

            const inParam = computeInParam(name);
            if (!inParam) return;

            const options = Array.from(sel.options || [])
                .map(o => ({ value: (o.value || '').trim(), label: (o.text || '').trim() }))
                .filter(it => !!it.value && it.value !== '---------');
            if (options.length === 0) return;

            // valores atuais (preferência: __in; fallback: __exact)
            const currentRaw = (urlParams.get(inParam) || urlParams.get(name) || '').trim();
            const currentSet = new Set(splitMulti(currentRaw));

            // tenta pegar um label mais amigável
            let labelText = '';
            try {
                const placeholder = (sel.options && sel.options.length > 0) ? (sel.options[0].text || '').trim() : '';
                // se o placeholder for tipo "Gênero" etc, usa como label
                if (placeholder && placeholder !== '---------' && !placeholder.includes('---') && !placeholder.toLowerCase().includes('selec')) {
                    labelText = placeholder;
                }
            } catch (e) {}
            if (!labelText) labelText = prettifyLabelFromName(name);

            const group = document.createElement('div');
            group.className = 'oc-multi-group';
            group.dataset.exactParam = name;
            group.dataset.inParam = inParam;

            const trigger = document.createElement('button');
            trigger.type = 'button';
            trigger.className = 'oc-ddmulti-trigger';
            trigger.setAttribute('aria-expanded', 'false');
            trigger.innerHTML = `<span class="oc-ddmulti-label"></span><span class="oc-ddmulti-arrow"></span>`;
            trigger.querySelector('.oc-ddmulti-label').innerText = labelText;

            const menu = document.createElement('div');
            menu.className = 'oc-ddmulti-menu';

            options.forEach((opt, idx) => {
                const id = `oc-multi-${inParam}-${idx}-${Math.random().toString(16).slice(2)}`;
                const row = document.createElement('label');
                row.className = 'oc-ddmulti-option';
                row.setAttribute('for', id);

                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.id = id;
                cb.value = opt.value;
                cb.checked = currentSet.has(opt.value);

                const span = document.createElement('span');
                span.innerText = opt.label;

                row.appendChild(cb);
                row.appendChild(span);
                menu.appendChild(row);
            });

            trigger.addEventListener('click', () => {
                const isOpen = group.classList.toggle('is-open');
                trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });

            group.appendChild(trigger);
            group.appendChild(menu);
            ui.appendChild(group);

            groups.push(group);

            // esconde o select original para não bagunçar o layout
            try { sel.style.setProperty('display', 'none', 'important'); } catch (e) {}
            // Select2 cria um container separado (span.select2/select2-container); esconder também
            try {
                const next = sel.nextElementSibling;
                if (next && next.classList && (next.classList.contains('select2') || next.classList.contains('select2-container'))) {
                    next.style.setProperty('display', 'none', 'important');
                }
            } catch (e) {}

            if (sel.dataset) sel.dataset.ocMultiConverted = '1';
        });

        if (groups.length === 0) return;

        const actions = document.createElement('div');
        actions.className = 'oc-multi-actions';

        const btnApply = document.createElement('button');
        btnApply.type = 'button';
        btnApply.className = 'btn btn-sm btn-primary';
        btnApply.innerText = 'Aplicar filtros';

        const btnClear = document.createElement('button');
        btnClear.type = 'button';
        btnClear.className = 'btn btn-sm btn-light';
        btnClear.innerText = 'Limpar';

        function applyAll(selectedMap) {
            const url = new URL(window.location.href);

            // remove todos os __in gerenciados e os __exact correspondentes
            groups.forEach(g => {
                const exactParam = g.dataset.exactParam;
                const inParam = g.dataset.inParam;
                if (exactParam) url.searchParams.delete(exactParam);
                if (inParam) url.searchParams.delete(inParam);
            });

            // aplica os selecionados
            Object.keys(selectedMap).forEach(inParam => {
                const vals = selectedMap[inParam] || [];
                if (vals.length > 0) {
                    url.searchParams.set(inParam, vals.join(','));
                }
            });

            url.searchParams.delete('p');
            window.location.href = url.toString();
        }

        btnApply.addEventListener('click', () => {
            const selectedMap = {};
            groups.forEach(g => {
                const inParam = g.dataset.inParam;
                if (!inParam) return;
                const vals = Array.from(g.querySelectorAll('input[type="checkbox"]:checked'))
                    .map(i => (i.value || '').trim())
                    .filter(Boolean);
                selectedMap[inParam] = vals;
            });
            applyAll(selectedMap);
        });

        btnClear.addEventListener('click', () => {
            groups.forEach(g => g.querySelectorAll('input[type="checkbox"]').forEach(i => { i.checked = false; }));
            applyAll({});
        });

        actions.appendChild(btnApply);
        actions.appendChild(btnClear);

        ui.appendChild(actions);

        // Inserir UI no topo do conteúdo da sidebar
        try {
            const filtersBox = sidebarContent.querySelector('.filter-group-box');
            if (filtersBox && filtersBox.insertAdjacentElement) {
                filtersBox.insertAdjacentElement('afterend', ui);
            } else {
                sidebarContent.insertBefore(ui, sidebarContent.firstChild);
            }
        } catch (e) {
            sidebarContent.appendChild(ui);
        }

        // Fechar menus ao clicar fora
        try {
            const handler = (ev) => {
                const openGroups = Array.from(sidebar.querySelectorAll('.oc-multi-group.is-open'));
                openGroups.forEach(g => {
                    if (g.contains(ev.target)) return;
                    g.classList.remove('is-open');
                    const t = g.querySelector('.oc-ddmulti-trigger');
                    if (t) t.setAttribute('aria-expanded', 'false');
                });
            };
            if (!sidebar.__ocOutsideClickBound) {
                sidebar.__ocOutsideClickBound = true;
                document.addEventListener('click', handler);
            }
        } catch (e) {}
    }

    function hasActiveFiltersForTopButton() {
        try {
            const sp = new URLSearchParams(window.location.search || '');
            for (const [k, v] of sp.entries()) {
                if (!v) continue;
                if (k === 'p' || k === 'o' || k === 'ot' || k === '_changelist_filters') continue;
                if (k === 'status__exact' || k === 'status') continue;
                return true;
            }
        } catch (e) {}
        return false;
    }

    function buildClearFiltersUrlPreservingStatus() {
        const cur = new URL(window.location.href);
        const sp = cur.searchParams;
        const st = (sp.get('status__exact') || sp.get('status') || 'aprovado').toString();
        const clean = new URL(cur.origin + cur.pathname);
        if (st) clean.searchParams.set('status__exact', st);
        return clean.toString();
    }

    function ensureTopClearFiltersButton() {
        try {
            const toolbar = document.getElementById('custom-filter-toolbar');
            if (!toolbar) return;
            const actions = toolbar.querySelector('.toolbar-actions');
            if (!actions) return;

            let btn = document.getElementById('btn-clear-filters-top');
            if (!btn) {
                btn = document.createElement('a');
                btn.id = 'btn-clear-filters-top';
                btn.className = 'btn btn-sm btn-light';
                btn.style.display = 'none';
                btn.style.whiteSpace = 'nowrap';
                btn.style.fontSize = '11px';
                btn.style.padding = '8px 12px';
                btn.style.borderRadius = '999px';
                btn.style.fontWeight = '800';
                btn.style.textTransform = 'uppercase';
                btn.style.letterSpacing = '0.4px';
                btn.innerText = 'Limpar filtros';

                const filtersBtn = document.getElementById('btn-open-sidebar');
                if (filtersBtn && filtersBtn.parentNode) {
                    filtersBtn.insertAdjacentElement('afterend', btn);
                } else {
                    actions.appendChild(btn);
                }
            }

            const active = hasActiveFiltersForTopButton();
            if (active) {
                btn.href = buildClearFiltersUrlPreservingStatus();
                btn.style.display = 'inline-flex';
                btn.style.alignItems = 'center';
            } else {
                btn.style.display = 'none';
            }
        } catch (e) {}
    }

    function buildFilterSidebar() {
        if (document.getElementById('custom-sidebar-filter')) return;

        // 1. ESTRUTURA
        const sidebar = document.createElement('div');
        sidebar.id = 'custom-sidebar-filter';
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <div class="sidebar-header-left">
                    <button type="button" id="btn-back-sidebar" aria-label="Voltar">←</button>
                    <h3>FILTROS DA AGÊNCIA</h3>
                </div>
            </div>
            <div id="sidebar-content">
                <div id="django-filters-target"></div>
                <div style="padding: 20px 0;">
                    <a href="." class="btn-clear-all" style="display:block; text-align:center; margin-top:15px; font-weight:bold; color:#f39c12; font-size:11px; text-decoration:none;">LIMPAR TUDO</a>
                </div>
            </div>
        `;
        document.body.appendChild(sidebar);
        // Sidebar criada

        const backdrop = document.createElement('div');
        backdrop.id = 'filter-backdrop';
        document.body.appendChild(backdrop);

        // Só seta + clique no backdrop fecham a sidebar
        backdrop.onclick = () => {
            setKeepSidebarOpen(false);
            window.closeSidebar();
        };

        // 2. SCANNER INTELIGENTE (SUPORTE A CARD DO JAZZMIN)
        const target = document.getElementById('django-filters-target');
        const container = document.getElementById('changelist-filter');

        if (container) {
            let foundItems = false;

            // ESTRATÉGIA A: Filtros Padrão Django (H3 + UL)
            const h3Elements = container.querySelectorAll('h3');
            const ulElements = container.querySelectorAll('ul');
            
            console.log('🔎 Procurando filtros - H3:', h3Elements.length, 'UL:', ulElements.length);
            
            if (h3Elements.length > 0 || ulElements.length > 0) {
                // Processa TODOS os H3 e UL
                let lastH3 = null;
                
                container.querySelectorAll('h3, ul').forEach((el, idx) => {
                    const txt = el.innerText.toLowerCase().trim();
                    
                    // Skip Ghost Filters (Ranges)
                    if (txt.includes('idade m') || txt.includes('peso m') || txt.includes('altura m') || txt.includes('sapato m')) {
                        console.log('⏭️ Pulando GhostFilter:', txt);
                        return;
                    }
                    
                    if (el.tagName === 'H3') {
                        console.log('📌 Encontrado H3:', txt);
                        const titleClone = el.cloneNode(true);
                        titleClone.style.fontSize = '0.75rem';
                        titleClone.style.fontWeight = '800';
                        titleClone.style.marginTop = '15px';
                        titleClone.style.color = '#555';
                        titleClone.style.textTransform = 'uppercase';
                        titleClone.style.marginBottom = '8px';
                        target.appendChild(titleClone);
                        lastH3 = titleClone;
                        foundItems = true;
                    } else if (el.tagName === 'UL') {
                        console.log('📋 Encontrado UL com', el.children.length, 'items');
                        const cloneUl = el.cloneNode(true);
                        cloneUl.style.paddingLeft = '0';
                        cloneUl.style.listStyle = 'none';
                        cloneUl.style.marginBottom = '12px';
                        cloneUl.querySelectorAll('li').forEach(li => {
                            li.style.marginBottom = '2px';
                            const a = li.querySelector('a');
                            if (a) {
                                a.style.display = 'block';
                                a.style.padding = '6px 0';
                                a.style.color = '#666';
                                a.style.fontSize = '0.85rem';
                                a.style.textDecoration = 'none';
                                a.style.transition = '0.2s';
                            }
                            if (li.classList.contains('selected')) {
                                if (a) {
                                    a.style.color = '#009688';
                                    a.style.fontWeight = 'bold';
                                }
                            }
                        });
                        target.appendChild(cloneUl);
                        foundItems = true;
                    }
                });
            }

            // ESTRATÉGIA B: Filtros Jazzmin Bootstrap (Card + Card-Header + Card-Body)
            if (!foundItems) {
                const cards = container.querySelectorAll('.card');
                console.log('🎴 Procurando Cards Jazzmin:', cards.length);
                if (cards.length > 0) {
                    processJazzminCards(cards, target);
                    foundItems = true;
                }
            }

            if (foundItems) {
                console.log('✅ Filtros encontrados e copiados para sidebar');
                // Esconde o container original SOMENTE se achamos e copiamos algo
                try { container.style.display = 'none'; } catch(e){}
            } else {
                console.log('⚠️ Nenhum filtro encontrado');
                target.innerHTML = "<p style='text-align:center; color:#999; font-size:11px;'>Nenhum filtro padrão encontrado.</p>";
            }
        } else {
            // Jazzmin pode não usar #changelist-filter. Sem drama: seguimos com os selects do topo.
            target.innerHTML = "";
        }

        // Além dos filtros padrão, mover selects/inputs visíveis da área principal para a sidebar
        try { copyVisibleSelectFiltersToTarget(target); } catch(e){ console.warn('copyVisibleSelectFiltersToTarget error', e); }

        // Auto-aplicar filtros ao selecionar
        try { bindSidebarFilterAutoApply(); } catch(e) {}

        isSidebarBuilt = true;
    }

    // Copia selects e inputs visíveis da área principal para a sidebar
    function copyVisibleSelectFiltersToTarget(target){
        if(!target) return;

        // 1) Melhor opção: mover o painel inteiro do topo (mantém o botão PESQUISAR e o layout original)
        if (moveMainFilterPanelIntoSidebar(target)) {
            // Se movemos o painel completo, não precisamos clonar itens soltos
            return;
        }

        // busca selects visíveis no formulário de listagem
        const form = document.getElementById('changelist-form');
        const candidates = [];
        if(form){
            form.querySelectorAll('select, input[type="text"], input[type="number"]').forEach(el => candidates.push(el));
            // também verifica elementos acima do form (alguns temas colocam filtros fora)
            let node = form.previousElementSibling;
            for(let i=0;i<3 && node;i++){ node.querySelectorAll && node.querySelectorAll('select, input[type="text"]').forEach(el=>candidates.push(el)); node = node.previousElementSibling; }
        }

        // fallback: pega selects visíveis na página, mas evita o select de ações
        if(candidates.length===0){
            document.querySelectorAll('select, input[type="text"], input[type="number"]').forEach(el=>candidates.push(el));
        }

        const movedContainers = new Set();
        candidates.forEach(el => {
            if(!el.offsetParent) return; // invisível
            if(el.name === 'action') return; // não mover dropdown de ações
            // evitar mover selects que já estão dentro da sidebar
            if(el.closest && el.closest('#custom-sidebar-filter')) return;
            // determinar bloco representativo para mover
            let block = el.closest('.filter-group-box') || el.closest('.field') || el.closest('label') || el.parentElement;
            if(!block) block = el.parentElement;
            if(movedContainers.has(block)) return;
            movedContainers.add(block);

            // clona e adiciona ao target
            const clone = block.cloneNode(true);
            // limpa ids duplicados
            clone.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
            const wrapper = document.createElement('div');
            wrapper.className = 'filter-group-box';
            // se block já tem um título, tenta extrair
            const titleText = (block.querySelector('label') && block.querySelector('label').innerText) || (block.querySelector('h3') && block.querySelector('h3').innerText) || '';
            if(titleText){
                const lbl = document.createElement('label'); lbl.innerText = titleText.trim(); wrapper.appendChild(lbl);
            }
            wrapper.appendChild(clone);
            target.appendChild(wrapper);

            // esconde o original para limpar a tela
            try { block.classList.add('hidden'); } catch(e){}
        });

        // por fim, tenta esconder o painel inteiro de filtros do topo (quando existir)
        hideMainFilterPanel();
    }

    // Encontra o painel principal de filtros (grid de selects + botão PESQUISAR)
    // mesmo quando estiver oculto (oc-main-filters-hidden).
    function findMainFilterPanelContainer() {
        // Prioridade 1: botão conhecido (id usado no CSS do projeto)
        const knownBtn = document.getElementById('btn-realizar-busca');
        if (knownBtn && !(knownBtn.closest && knownBtn.closest('#custom-sidebar-filter'))) {
            let node = knownBtn.parentElement;
            let guard = 0;
            while (node && guard++ < 14) {
                if (node.closest && node.closest('#custom-sidebar-filter')) break;
                const selectCount = node.querySelectorAll ? node.querySelectorAll('select').length : 0;
                if (selectCount >= 3) {
                    // pega o container mais próximo do botão, não sobe até pegar o "corpo todo"
                    return node;
                }
                node = node.parentElement;
            }
        }

        function hasResultsTable(el) {
            try {
                return !!(el && el.querySelector && (el.querySelector('#result_list') || el.querySelector('.results')));
            } catch (e) {
                return false;
            }
        }

        function isSearchTrigger(el) {
            if (!el) return false;
            if (el.closest && el.closest('#custom-sidebar-filter')) return false;
            const txt = ((el.innerText || el.value || '') + '').toLowerCase();
            return txt.includes('pesquisar');
        }

        // Fallback: acha um botão/link/submit com texto PESQUISAR fora da sidebar e sobe até um container com muitos selects
        const searchButtons = Array.from(document.querySelectorAll('button, a, input[type="submit"], input[type="button"], [role="button"]'))
            .filter(b => {
                if (!b) return false;
                if (b.closest && b.closest('#custom-sidebar-filter')) return false;
                return isSearchTrigger(b);
            });

        let best = null;
        let bestScore = 0;
        for (const btn of searchButtons) {
            let node = btn.parentElement;
            let guard = 0;
            let firstCandidate = null;

            while (node && guard++ < 20) {
                if (node.closest && node.closest('#custom-sidebar-filter')) break;
                if (hasResultsTable(node)) break;

                const selects = node.querySelectorAll
                    ? Array.from(node.querySelectorAll('select')).filter(s => s && s.name !== 'action').length
                    : 0;
                const hasSearch = node.querySelector
                    ? !!Array.from(node.querySelectorAll('button, a, input[type="submit"], input[type="button"], [role="button"]')).find(isSearchTrigger)
                    : false;

                if (selects >= 3 && hasSearch) {
                    firstCandidate = node;
                    break;
                }
                node = node.parentElement;
            }

            if (firstCandidate) {
                const selects = firstCandidate.querySelectorAll
                    ? Array.from(firstCandidate.querySelectorAll('select')).filter(s => s && s.name !== 'action').length
                    : 0;
                const score = selects * 10 + 200;
                if (score > bestScore) {
                    bestScore = score;
                    best = firstCandidate;
                }
            }
        }

        return best;
    }

    // Move o painel de filtros do topo (grid de selects + botão PESQUISAR) para dentro da sidebar.
    // Retorna true se conseguiu mover.
    function moveMainFilterPanelIntoSidebar(target) {
        if (!target) return false;
        // evita mover duas vezes
        if (target.querySelector && target.querySelector('.oc-moved-main-filters')) return true;

        const panel = findMainFilterPanelContainer();
        if (!panel) return false;
        if (panel.closest && panel.closest('#custom-sidebar-filter')) return true;

        const wrapper = document.createElement('div');
        wrapper.className = 'filter-group-box oc-moved-main-filters';
        const label = document.createElement('label');
        label.innerText = 'Filtros';
        wrapper.appendChild(label);

        // Marca o painel original para estilização dentro da sidebar (sem esconder)
        try {
            panel.classList.add('oc-main-filters-panel');
            panel.classList.remove('oc-main-filters-hidden');
            // garante visibilidade mesmo se o tema/CSS tiver escondido
            panel.style.setProperty('display', 'block', 'important');
        } catch (e) {}

        wrapper.appendChild(panel);
        target.appendChild(wrapper);
        return true;
    }

    // Esconde o painel de filtros do topo (onde ficam vários selects + botão PESQUISAR)
    function hideMainFilterPanel() {
        const panel = findMainFilterPanelContainer();
        if (!panel) return;
        // Não ocultar se já estiver dentro da sidebar
        if (panel.closest && panel.closest('#custom-sidebar-filter')) return;
        if (!(panel.classList && panel.classList.contains('oc-main-filters-hidden'))) {
            panel.classList.add('oc-main-filters-hidden');
        }
        try { panel.style.setProperty('display', 'none', 'important'); } catch(e) {}
    }

    // --- PROCESSADORES DE HTML ---
    
    function processJazzminCards(cards, target) {
        cards.forEach(card => {
            const header = card.querySelector('.card-header');
            const body = card.querySelector('.card-body');
            
            if (header && body) {
                // Título
                const title = document.createElement('h3');
                title.innerText = header.innerText.trim();
                const txt = title.innerText.toLowerCase();
                if (txt.includes('idade m') || txt.includes('peso m') || txt.includes('altura m') || txt.includes('sapato m')) return;

                title.style.fontSize = '0.75rem'; title.style.fontWeight = '800'; 
                title.style.marginTop = '15px'; title.style.color = '#555'; 
                title.style.textTransform = 'uppercase';
                target.appendChild(title);

                // Lista
                const ul = body.querySelector('ul');
                if (ul) {
                    const cloneUl = ul.cloneNode(true);
                    cloneUl.style.paddingLeft = '0'; cloneUl.style.listStyle = 'none';
                    cloneUl.querySelectorAll('li a').forEach(a => {
                        a.style.display = 'block'; a.style.padding = '4px 0'; a.style.color = '#666';
                        if (a.parentElement.classList.contains('selected')) { a.style.color = '#009688'; a.style.fontWeight = 'bold'; }
                    });
                    target.appendChild(cloneUl);
                }
            }
        });
    }

    // --- SETUP UI & TOOLS ---

    function buildLiveSearchUrl(query) {
        const q = (query || '').toString().trim();
        const url = new URL(window.location.href);
        if (q) url.searchParams.set('q', q);
        else url.searchParams.delete('q');
        // volta pra primeira página quando muda busca
        url.searchParams.delete('p');
        return url;
    }

    async function applyLiveSearch(query) {
        const nextQ = (query || '').toString().trim();
        const currentQ = new URLSearchParams(window.location.search).get('q') || '';

        if (nextQ === currentQ && nextQ === liveSearchLastApplied) return;
        liveSearchLastApplied = nextQ;

        const url = buildLiveSearchUrl(nextQ);

        // Mantém o foco e cursor no input enquanto atualiza a lista
        const input = document.getElementById('oc-live-search');
        const selectionStart = input ? input.selectionStart : null;
        const selectionEnd = input ? input.selectionEnd : null;
        const hadFocus = input ? (document.activeElement === input) : false;

        // Cancela a requisição anterior (digitação rápida)
        try {
            if (liveSearchAbortController) liveSearchAbortController.abort();
        } catch (e) {}
        liveSearchAbortController = new AbortController();

        function storeRestoreForReload() {
            try {
                const payload = {
                    v: nextQ,
                    t: Date.now(),
                    s: input ? input.selectionStart : null,
                    e: input ? input.selectionEnd : null,
                    f: input ? (document.activeElement === input) : false
                };
                sessionStorage.setItem('__oc_live_search_restore', JSON.stringify(payload));
            } catch (e) {}
        }

        try {
            const res = await fetch(url.toString(), {
                signal: liveSearchAbortController.signal,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const html = await res.text();
            const doc = new DOMParser().parseFromString(html, 'text/html');

            let didUpdate = false;

            // Preferência 1: trocar o bloco .results
            const newResults = doc.querySelector('#changelist-form .results') || doc.querySelector('.results');
            const curResults = document.querySelector('#changelist-form .results') || document.querySelector('.results');
            if (newResults && curResults) {
                curResults.replaceWith(newResults);
                didUpdate = true;
            } else {
                // Preferência 2: trocar só a tabela #result_list (Jazzmin/Django)
                const newTable = doc.querySelector('#result_list');
                const curTable = document.querySelector('#result_list');
                if (newTable && curTable) {
                    const newWrap = newTable.closest('.results') || newTable.parentElement;
                    const curWrap = curTable.closest('.results') || curTable.parentElement;
                    if (newWrap && curWrap) {
                        curWrap.replaceWith(newWrap);
                        didUpdate = true;
                    }
                }
            }

            const newPaginator = doc.querySelector('.paginator');
            const curPaginator = document.querySelector('.paginator');
            if (newPaginator && curPaginator) {
                curPaginator.replaceWith(newPaginator);
            } else if (newPaginator && !curPaginator) {
                // alguns temas só renderizam paginator em certos casos
                const changelist = document.getElementById('changelist') || document.body;
                changelist.appendChild(newPaginator);
            } else if (!newPaginator && curPaginator) {
                curPaginator.remove();
            }

            // Se não conseguimos atualizar a lista no DOM, faz fallback para reload normal
            if (!didUpdate) {
                throw new Error('DOM update failed');
            }

            // Atualiza a URL sem recarregar (evita perder foco)
            window.history.replaceState({}, '', url.toString());

            // Reaplica regras de UI que podem depender do DOM (pós-replace)
            try { ensureDjangoActionsCounter(); } catch(e) {}
            try { hideMainFilterPanel(); } catch(e) {}
            try { ensureTopClearFiltersButton(); } catch(e) {}

            // Mantém o foco no input
            if (input && hadFocus) {
                input.focus({ preventScroll: true });
                if (selectionStart !== null && selectionEnd !== null) {
                    try { input.setSelectionRange(selectionStart, selectionEnd); } catch(e) {}
                }
            }
        } catch (e) {
            // Se foi abort, ignora
            if (e && (e.name === 'AbortError')) return;
            // fallback: navega normalmente (evita ficar sem atualizar)
            try {
                storeRestoreForReload();
                window.location.assign(url.toString());
            } catch (err) {}
        }
    }

    function ensureLiveSearchInput() {
        const input = document.getElementById('oc-live-search');
        if (!input) return;
        if (input.dataset.bound === '1') return;
        input.dataset.bound = '1';

        // pré-preenche com a busca atual
        try {
            const params = new URLSearchParams(window.location.search);
            const currentQ = params.get('q') || '';
            if (currentQ && !input.value) input.value = currentQ;
        } catch(e) {}

        input.addEventListener('input', () => {
            if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                applyLiveSearch(input.value);
            }, 350);
        });

        input.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                ev.preventDefault();
                if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
                applyLiveSearch(input.value);
            }
        });

        // Restaura foco/cursor após reload disparado pela busca
        try {
            const raw = sessionStorage.getItem('__oc_live_search_restore');
            if (raw) {
                const payload = JSON.parse(raw);
                sessionStorage.removeItem('__oc_live_search_restore');
                if (payload && payload.t && (Date.now() - payload.t) <= 5000) {
                    if (typeof payload.v === 'string' && payload.v && !input.value) input.value = payload.v;
                    if (payload.f) {
                        input.focus({ preventScroll: true });
                        const s = (payload.s !== null && payload.s !== undefined) ? payload.s : input.value.length;
                        const e = (payload.e !== null && payload.e !== undefined) ? payload.e : input.value.length;
                        try { input.setSelectionRange(s, e); } catch(ex) {}
                    }
                }
            }
        } catch(e) {}
    }

    function applyUserProfileStatusDotForMobile() {
        try {
            // Verifica se estamos na página correta (mais genérico para garantir)
            if (!window.location.pathname.includes('/core/userprofile/')) return;
            
            // Aumenta o range para pegar tablets e celulares grandes
            if (window.innerWidth > 900) return;

            const rows = document.querySelectorAll('#result_list tr');
            rows.forEach(row => {
                const td = row.querySelector('td.field-nome_com_status');
                if (!td) return;

                // Se o badge estiver fora do link, também some
                td.querySelectorAll('.oc-status-badge').forEach(b => {
                    if (b.getAttribute('data-mobile-processed') === 'true') return;
                    b.style.setProperty('display', 'none', 'important');
                    b.setAttribute('data-mobile-processed', 'true');
                });

                // Tenta pegar o badge (último span dentro do link)
                const link = td.querySelector('a');
                if (!link) return;
                
                const spans = link.querySelectorAll('span');
                if (spans.length < 2) return;

                // No mobile queremos apenas o nome: esconde todos os spans após o primeiro
                let changed = false;
                spans.forEach((sp, idx) => {
                    if (idx === 0) return;
                    if (sp.getAttribute('data-mobile-processed') === 'true') return;
                    sp.style.setProperty('display', 'none', 'important');
                    sp.setAttribute('data-mobile-processed', 'true');
                    changed = true;
                });

                // Marca o TD também para evitar reprocessamento excessivo
                if (changed) td.setAttribute('data-mobile-processed', 'true');
            });
        } catch(e) {
            console.error('Erro no fix mobile:', e);
        }
    }

    function setupUI() {
        // Importante: este setup roda em interval. Qualquer exceção aqui não pode quebrar a toolbar.
        try { ensureDjangoActionsCounter(); } catch(e) {}

        const path = (window.location && window.location.pathname) ? window.location.pathname : '';
        const isUserProfileChangeList = path.includes('/admin/core/userprofile/');

        // Se já criamos uma toolbar em outra tela (Trabalhos/Candidaturas/etc), remove.
        // Regras daqui valem só para Base de Promotores.
        try {
            const existingToolbar = document.getElementById('custom-filter-toolbar');
            if (existingToolbar && !isUserProfileChangeList) {
                existingToolbar.remove();
            }
        } catch (e) {}

        // Marca contexto da página para CSS responsivo (PythonAnywhere/mobile)
        try {
            if (document.body && document.body.classList) {
                if (path.includes('/admin/core/userprofile/') && document.body.classList.contains('change-list')) {
                    document.body.classList.add('oc-userprofile-changelist');
                }
            }
        } catch(e) {}

        // Cria toolbar (tabs + busca + botão filtros) - SOMENTE Base de Promotores
        try {
            if (!isUserProfileChangeList) {
                // não mexer em outras telas
            } else if (!document.getElementById('custom-filter-toolbar')) {
                const form = document.getElementById('changelist-form');
                if (form) {
                    const toolbar = document.createElement('div');
                    toolbar.id = 'custom-filter-toolbar';
                    toolbar.innerLoc = '1';
                    toolbar.innerHTML = `
                        <div class="toolbar-actions">
                            <div class="oc-toolbar-left">
                                <div class="oc-status-tabs" id="oc-status-tabs" style="display:none;">
                                    <a class="oc-status-tab" id="oc-tab-aprovados" href="/admin/core/userprofile/aprovados/">Aprovados</a>
                                    <a class="oc-status-tab" id="oc-tab-pendentes" href="/admin/core/userprofile/pendentes/">Pendentes</a>
                                    <a class="oc-status-tab" id="oc-tab-correcao" href="/admin/core/userprofile/aguardando-ajuste/">Aguardando ajuste</a>
                                </div>
                            </div>

                            <div class="oc-toolbar-center">
                                <input id="oc-live-search" type="search" placeholder="Pesquisar (nome, CPF, WhatsApp...)" autocomplete="off" />
                            </div>

                            <div class="oc-toolbar-right" id="oc-toolbar-right">
                                <button type="button" id="btn-open-sidebar" class="btn-filtros-avancados">Filtros</button>
                                <button type="button" id="btn-gerar-apresentacao" class="btn btn-sm btn-primary">Gerar link de apresentação</button>
                                <button type="button" id="btn-limpar-selecao" class="btn btn-sm btn-light">Limpar seleção</button>
                            </div>
                        </div>
                    `;
                    if (form.parentNode) {
                        form.parentNode.insertBefore(toolbar, form);
                    }
                }
            }

            // Se a toolbar já existia (de uma versão anterior do JS), injeta botões faltantes
            if (isUserProfileChangeList) {
                const toolbar = document.getElementById('custom-filter-toolbar');
                if (toolbar) {
                    const rightRow = document.getElementById('oc-toolbar-right') || toolbar.querySelector('.oc-toolbar-right') || toolbar.querySelector('.toolbar-actions') || toolbar;

                    if (!document.getElementById('btn-gerar-apresentacao')) {
                        const b = document.createElement('button');
                        b.type = 'button';
                        b.id = 'btn-gerar-apresentacao';
                        b.className = 'btn btn-sm btn-primary';
                        b.textContent = 'Gerar link de apresentação';
                        rightRow.appendChild(b);
                    }

                    if (!document.getElementById('btn-limpar-selecao')) {
                        const b = document.createElement('button');
                        b.type = 'button';
                        b.id = 'btn-limpar-selecao';
                        b.className = 'btn btn-sm btn-light';
                        b.textContent = 'Limpar seleção';
                        rightRow.appendChild(b);
                    }
                }
            }

            // Garante handler do botão filtros (mesmo se toolbar já existia)
            const btn = document.getElementById('btn-open-sidebar');
            if (btn && btn.dataset.bound !== '1') {
                btn.dataset.bound = '1';
                btn.addEventListener('click', () => window.openCastingFilters());
            }

            function getSelectedCount() {
                try {
                    return document.querySelectorAll('input[name="_selected_action"]:checked').length;
                } catch (e) {
                    return 0;
                }
            }

            // Seleção persistente (para poder pesquisar e ir marcando vários)
            const SELECT_KEY = '__oc_selected_userprofile_ids';

            function readStoredSelectedIds() {
                try {
                    const raw = sessionStorage.getItem(SELECT_KEY);
                    if (!raw) return [];
                    const parsed = JSON.parse(raw);
                    if (!Array.isArray(parsed)) return [];
                    return parsed.map(String).filter(Boolean);
                } catch (e) {
                    return [];
                }
            }

            function writeStoredSelectedIds(ids) {
                try {
                    const unique = Array.from(new Set((ids || []).map(String).filter(Boolean)));
                    sessionStorage.setItem(SELECT_KEY, JSON.stringify(unique));
                } catch (e) {}
            }

            function addStoredSelectedId(id) {
                const ids = readStoredSelectedIds();
                const sid = String(id || '').trim();
                if (!sid) return;
                if (!ids.includes(sid)) {
                    ids.push(sid);
                    writeStoredSelectedIds(ids);
                }
            }

            function removeStoredSelectedId(id) {
                const sid = String(id || '').trim();
                if (!sid) return;
                const ids = readStoredSelectedIds().filter(x => x !== sid);
                writeStoredSelectedIds(ids);
            }

            function getStoredSelectedCount() {
                return readStoredSelectedIds().length;
            }

            function applyStoredSelectionToVisibleRows() {
                try {
                    const ids = new Set(readStoredSelectedIds());
                    const boxes = document.querySelectorAll('input[name="_selected_action"]');
                    boxes.forEach(b => {
                        const v = String(b.value || '');
                        if (!v) return;
                        if (ids.has(v)) b.checked = true;
                    });
                } catch (e) {}
            }

            function setApresentacaoButtonVisible(flag) {
                const b = document.getElementById('btn-gerar-apresentacao');
                if (!b) return;
                b.style.display = flag ? 'inline-flex' : 'none';
            }

            function setLimparSelecaoButtonVisible(flag) {
                const b = document.getElementById('btn-limpar-selecao');
                if (!b) return;
                b.style.display = flag ? 'inline-flex' : 'none';
            }

            function submitAdminAction(actionName) {
                const form = document.getElementById('changelist-form');
                if (!form) return false;

                const sel = document.querySelector('select[name="action"]');
                if (!sel) return false;

                // Injeta inputs ocultos para IDs selecionados que NÃO estão visíveis na tabela atual.
                // Isso permite selecionar via pesquisa e depois gerar um link com todos.
                try {
                    // remove anteriores
                    form.querySelectorAll('input[data-oc-persist="1"]').forEach(n => n.remove());

                    const stored = readStoredSelectedIds();
                    if (stored && stored.length) {
                        const present = new Set();
                        form.querySelectorAll('input[name="_selected_action"]').forEach(cb => {
                            if (cb && cb.value) present.add(String(cb.value));
                        });

                        stored.forEach(id => {
                            const sid = String(id);
                            if (!sid) return;
                            if (present.has(sid)) return; // já existe checkbox na tela

                            const h = document.createElement('input');
                            h.type = 'hidden';
                            h.name = '_selected_action';
                            h.value = sid;
                            h.setAttribute('data-oc-persist', '1');
                            form.appendChild(h);
                        });
                    }
                } catch (e) {}

                sel.value = actionName;
                try {
                    form.submit();
                    return true;
                } catch (e) {
                    return false;
                }
            }

            // Botão de gerar link de apresentação (usa a action do Django por trás)
            const btnAp = document.getElementById('btn-gerar-apresentacao');
            if (btnAp && btnAp.dataset.bound !== '1') {
                btnAp.dataset.bound = '1';
                btnAp.addEventListener('click', () => {
                    const path = (window.location && window.location.pathname) ? window.location.pathname : '';
                    if (!path.includes('/admin/core/userprofile/')) return;

                    const selected = getStoredSelectedCount() || getSelectedCount();
                    if (!selected) {
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                icon: 'warning',
                                title: 'Selecione pelo menos 1 promotor',
                                text: 'Marque o checkbox de quem você quer enviar para o cliente.',
                                heightAuto: false,
                                customClass: { popup: 'oc-swal-popup' },
                            });
                        } else {
                            alert('Selecione pelo menos 1 promotor (checkbox).');
                        }
                        return;
                    }

                    const ok = submitAdminAction('gerar_link_apresentacao');
                    if (!ok) {
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                icon: 'error',
                                title: 'Não foi possível gerar',
                                text: 'Não encontrei o seletor de ações do Django na página.',
                                heightAuto: false,
                                customClass: { popup: 'oc-swal-popup' },
                            });
                        } else {
                            alert('Não foi possível gerar o link (ações do Django não encontradas).');
                        }
                    }
                });
            }

            // Botão limpar seleção (zera seleção persistida e desmarca visíveis)
            const btnClearSel = document.getElementById('btn-limpar-selecao');
            if (btnClearSel && btnClearSel.dataset.bound !== '1') {
                btnClearSel.dataset.bound = '1';
                btnClearSel.addEventListener('click', () => {
                    try {
                        sessionStorage.removeItem(SELECT_KEY);
                    } catch (e) {}

                    try {
                        document.querySelectorAll('input[name="_selected_action"]:checked').forEach(cb => {
                            cb.checked = false;
                        });
                    } catch (e) {}

                    // Desmarca "selecionar todos" se existir
                    try {
                        const t = document.getElementById('action-toggle');
                        if (t) t.checked = false;
                    } catch (e) {}

                    // Remove hidden persistidos (se existirem)
                    try {
                        const form = document.getElementById('changelist-form');
                        if (form) form.querySelectorAll('input[data-oc-persist="1"]').forEach(n => n.remove());
                    } catch (e) {}

                    setApresentacaoButtonVisible(false);
                    setLimparSelecaoButtonVisible(false);
                });
            }

            // Mostrar/esconder o botão conforme seleção (sem mexer na posição das abas)
            try {
                const path = (window.location && window.location.pathname) ? window.location.pathname : '';
                if (path.includes('/admin/core/userprofile/')) {
                    const form = document.getElementById('changelist-form');
                    // Estado inicial
                    applyStoredSelectionToVisibleRows();
                    const hasAny = (getStoredSelectedCount() > 0 || getSelectedCount() > 0);
                    setApresentacaoButtonVisible(hasAny);
                    setLimparSelecaoButtonVisible(hasAny);

                    if (form && form.dataset.ocBoundApSel !== '1') {
                        form.dataset.ocBoundApSel = '1';
                        // Captura mudanças de qualquer checkbox (inclui "selecionar todos")
                        form.addEventListener('change', (ev) => {
                            const t = ev && ev.target;
                            if (t && t.matches && t.matches('input[name="_selected_action"]')) {
                                if (t.checked) addStoredSelectedId(t.value);
                                else removeStoredSelectedId(t.value);
                                const has = getStoredSelectedCount() > 0;
                                setApresentacaoButtonVisible(has);
                                setLimparSelecaoButtonVisible(has);
                            } else if (t && t.matches && t.matches('#action-toggle')) {
                                // Selecionar tudo (na visão atual): adiciona/remove os visíveis
                                const boxes = document.querySelectorAll('input[name="_selected_action"]');
                                boxes.forEach(cb => {
                                    if (!cb || !cb.value) return;
                                    if (t.checked) addStoredSelectedId(cb.value);
                                    else removeStoredSelectedId(cb.value);
                                });
                                const has = getStoredSelectedCount() > 0;
                                setApresentacaoButtonVisible(has);
                                setLimparSelecaoButtonVisible(has);
                            }
                        }, true);
                    }
                }
            } catch (e) {}
        } catch(e) {
            console.error('setupUI toolbar error', e);
        }

        // Popup bonito do link gerado (substitui a barra verde)
        try {
            const path = (window.location && window.location.pathname) ? window.location.pathname : '';
            if (path.includes('/admin/core/userprofile/')) {
                if (!window.__oc_apresentacao_popup_done) {
                    const candidates = Array.from(document.querySelectorAll(
                        '.messagelist li, .messagelist .success, .messagelist .warning, .alert, .alert-success, .alert-warning'
                    ));

                    let successNode = null;
                    let warningNode = null;
                    let href = null;

                    for (const el of candidates) {
                        const a = el.querySelector && el.querySelector('a[href*="/apresentacao/"]');
                        if (a && a.getAttribute('href')) {
                            href = a.getAttribute('href');
                            successNode = el;
                            break;
                        }
                    }

                    // Pega aviso de "ignorados" se existir
                    for (const el of candidates) {
                        const txt = (el.innerText || '').toLowerCase();
                        if (txt.includes('foram ignorados')) {
                            warningNode = el;
                            break;
                        }
                    }

                    if (href && successNode && typeof Swal !== 'undefined') {
                        window.__oc_apresentacao_popup_done = true;

                        // Remove mensagens da tela
                        try { successNode.remove(); } catch (e) { try { successNode.style.display = 'none'; } catch (e2) {} }
                        if (warningNode) {
                            try { warningNode.remove(); } catch (e) { try { warningNode.style.display = 'none'; } catch (e2) {} }
                        }

                        const warnText = warningNode ? (warningNode.innerText || '').trim() : '';
                        const safeWarn = warnText ? `<div style="margin-top:10px; font-weight:800; color:#8a6d3b;">${warnText}</div>` : '';

                        const html = `
                            <div style="text-align:left;">
                                <div style="font-weight:900; margin-bottom:8px;">Link de apresentação gerado</div>
                                <div style="font-size:12px; color:#6c757d; margin-bottom:10px;">Este link expira em 7 dias.</div>
                                <input id="oc-ap-link" class="swal2-input" style="margin:0;" readonly value="${href.replace(/"/g,'&quot;')}">
                                ${safeWarn}
                            </div>
                        `;

                        Swal.fire({
                            icon: 'success',
                            title: '',
                            html,
                            confirmButtonText: 'Copiar link',
                            showCancelButton: true,
                            cancelButtonText: 'Fechar',
                            heightAuto: false,
                            customClass: { popup: 'oc-swal-popup' },
                            didOpen: () => {
                                try {
                                    const i = document.getElementById('oc-ap-link');
                                    if (i) i.select();
                                } catch (e) {}
                            },
                            preConfirm: async () => {
                                try {
                                    const text = href;
                                    if (navigator.clipboard && navigator.clipboard.writeText) {
                                        await navigator.clipboard.writeText(text);
                                        return true;
                                    }
                                } catch (e) {}

                                // fallback
                                try {
                                    const ta = document.createElement('textarea');
                                    ta.value = href;
                                    ta.setAttribute('readonly', 'readonly');
                                    ta.style.position = 'fixed';
                                    ta.style.left = '-9999px';
                                    document.body.appendChild(ta);
                                    ta.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(ta);
                                    return true;
                                } catch (e) {
                                    return true;
                                }
                            }
                        }).then((r) => {
                            // Ao clicar em copiar, o Swal fecha automaticamente.
                            // Nada extra aqui.
                        });
                    }
                }
            }
        } catch (e) {}

        // Botão pequeno "Limpar filtros" no topo (só aparece quando houver filtros ativos)
        try { ensureTopClearFiltersButton(); } catch(e) {}

        // Tabs Aprovados/Pendentes no topo (somente na Base de Promotores)
        try {
            const path = (window.location && window.location.pathname) ? window.location.pathname : '';
            if (path.includes('/admin/core/userprofile/')) {
                const tabs = document.getElementById('oc-status-tabs');
                if (tabs) {
                    tabs.style.display = 'flex';
                    const sp = new URLSearchParams(window.location.search || '');
                    const st = (sp.get('status__exact') || sp.get('status') || 'aprovado').toLowerCase();
                    const a = document.getElementById('oc-tab-aprovados');
                    const p = document.getElementById('oc-tab-pendentes');
                    const c = document.getElementById('oc-tab-correcao');
                    if (a) a.classList.toggle('is-active', st === 'aprovado');
                    if (p) p.classList.toggle('is-active', st === 'pendente');
                    if (c) c.classList.toggle('is-active', st === 'correcao');
                }
            }
        } catch(e) {}

        // garante o live-search mesmo se o toolbar já existia
        try { ensureLiveSearchInput(); } catch(e) {}

        // Mensagem quando não houver resultados (evita tela branca)
        try { ensureNoResultsMessage(); } catch(e) {}

        // Mobile: usa bolinha colorida no lugar do texto do status
        try { applyUserProfileStatusDotForMobile(); } catch(e) {}

        // Hover Menus
        try {
            document.querySelectorAll('.btn-group-custom').forEach(g => {
                const d = g.querySelector('.dropdown-content');
                if(d) { g.onmouseenter = () => d.style.display='block'; g.onmouseleave = () => d.style.display='none'; }
            });
        } catch(e) {}

        // Garante que o painel do topo fique oculto SEMPRE (inclusive após clicar em PESQUISAR e recarregar)
        try { hideMainFilterPanel(); } catch(e){}

        // Se a aplicação automática pediu para manter a sidebar aberta, reabre após reload.
        try {
            if (shouldKeepSidebarOpen()) {
                // pequena espera para o DOM estabilizar
                setTimeout(() => {
                    try { window.openCastingFilters(); } catch (e) {}
                }, 120);
            }
        } catch (e) {}
    }

    // --- FERRAMENTAS EXTRAS ---
    window.selecionarTudo = (s) => document.querySelectorAll('.swal-copy-grid input').forEach(c => c.checked = s);
    function checkHtml(d) {
        // Normaliza para suportar chaves antigas/novas do template
        const normalized = {
            ...d,
            is_pcd: d?.is_pcd ?? d?.pcd,
            descricao_pcd: d?.descricao_pcd ?? d?.pcd_desc,
            pix: d?.pix ?? d?.chave_pix,
            tipo_chave_pix: d?.tipo_chave_pix,
        };

        const enderecoCompleto = [d.endereco, d.numero, d.bairro, d.cidade, d.estado, d.cep]
            .filter(Boolean)
            .join(', ')
            .replace(/\s+,/g, ',');

        const fields = [
            // Padrão (pré-selecionado): nome, cpf, endereço, sexo
            { k: 'nome', f: 'Nome', v: d.nome, on: true },
            { k: 'cpf', f: 'CPF', v: d.cpf, on: true },
            { k: 'endereco', f: 'Endereço', v: enderecoCompleto || '---', on: true },
            { k: 'sexo', f: 'Sexo', v: d.genero, on: true },

            // Contato
            { k: 'whatsapp', f: 'WhatsApp', v: d.whatsapp },
            { k: 'email', f: 'E-mail', v: d.email },
            { k: 'instagram', f: 'Instagram', v: d.instagram },

            // Pessoal
            { k: 'nascimento', f: 'Nascimento', v: d.nascimento },
            { k: 'idade', f: 'Idade', v: d.idade },
            { k: 'rg', f: 'RG', v: d.rg },
            { k: 'nacionalidade', f: 'Nacionalidade', v: d.nacionalidade },
            { k: 'etnia', f: 'Cor/Etnia', v: d.etnia },
            { k: 'pcd', f: 'PCD', v: normalized.is_pcd },
            { k: 'pcd_desc', f: 'Descrição PCD', v: normalized.descricao_pcd },

            // Medidas & visual
            { k: 'altura', f: 'Altura', v: d.altura },
            { k: 'peso', f: 'Peso', v: d.peso },
            { k: 'manequim', f: 'Manequim', v: d.manequim },
            { k: 'camiseta', f: 'Camiseta', v: d.camiseta },
            { k: 'calcado', f: 'Calçado', v: d.calcado },
            { k: 'olhos', f: 'Olhos', v: d.olhos },
            { k: 'cabelo', f: 'Cabelo', v: d.cabelo },

            // Profissional
            { k: 'experiencia', f: 'Experiência', v: d.experiencia },
            { k: 'disponibilidade', f: 'Disponibilidade', v: d.disponibilidade },
            { k: 'areas', f: 'Áreas de atuação', v: d.areas_atuacao },

            // Idiomas
            { k: 'ingles', f: 'Inglês', v: d.ingles },
            { k: 'espanhol', f: 'Espanhol', v: d.espanhol },
            { k: 'frances', f: 'Francês', v: d.frances },
            { k: 'outros_idiomas', f: 'Outros idiomas', v: d.outros_idiomas },

            // Bancário
            { k: 'banco', f: 'Banco', v: d.banco },
            { k: 'tipo_conta', f: 'Tipo de conta', v: d.tipo_conta },
            { k: 'agencia', f: 'Agência', v: d.agencia },
            { k: 'conta', f: 'Conta', v: d.conta },
            { k: 'pix_tipo', f: 'Tipo chave PIX', v: normalized.tipo_chave_pix },
            { k: 'pix', f: 'Chave PIX', v: normalized.pix },

            // Meta
            { k: 'uuid', f: 'UUID', v: d.uuid },
        ].filter(x => x && x.f);

        const items = fields.map(x => {
            const safeValue = (x.v === undefined || x.v === null || String(x.v).trim() === '') ? '---' : String(x.v);
            const checked = x.on ? 'checked' : '';
            return `
                <label class="cp-item" style="display:flex; gap:10px; align-items:flex-start; padding:10px; border:1px solid #eee; border-radius:12px; background:#fff;">
                    <input type="checkbox" data-k="${x.k}" data-f="${x.f}" data-v="${safeValue.replace(/"/g, '&quot;')}" ${checked} style="margin-top:2px;">
                    <span style="display:block;">
                        <div style="font-weight:900; font-size:12px; text-transform:uppercase; letter-spacing:0.4px; color:#566;">${x.f}</div>
                        <div style="font-weight:700; color:#2c3e50; word-break:break-word;">${safeValue}</div>
                    </span>
                </label>
            `;
        }).join('');

        return `
            <div>
                <div class="oc-swal-actions">
                    <button type="button" class="oc-swal-chip" id="oc-btn-select-all">Selecionar tudo</button>
                    <button type="button" class="oc-swal-chip primary" id="oc-btn-preset">Informações padrão</button>
                </div>
                <div class="swal-copy-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;text-align:left; max-height:55vh; overflow:auto; padding-right:4px;">
                    ${items}
                </div>
            </div>
        `;
    }

    function applyPresetPadrao() {
        // padrão: nome, cpf, endereco, sexo
        const keys = new Set(['nome', 'cpf', 'endereco', 'sexo']);
        document.querySelectorAll('.swal-copy-grid input[type="checkbox"]').forEach(c => {
            c.checked = keys.has(c.dataset.k);
        });
    }
    window.copiarInformacoesPerfil = function(d) {
        Swal.fire({
            title: 'Enviar Informações',
            html: `<div class="oc-swal-form">${checkHtml(d)}</div>`,
            width: 'min(980px, 94vw)',
            heightAuto: false,
            scrollbarPadding: false,
            customClass: { popup: 'oc-swal-popup' },
            showCancelButton: true,
            confirmButtonText: 'COPIAR',
            cancelButtonText: 'Cancelar',
            didOpen: () => {
                try {
                    const btnAll = document.getElementById('oc-btn-select-all');
                    const btnPreset = document.getElementById('oc-btn-preset');
                    if (btnAll) btnAll.addEventListener('click', () => window.selecionarTudo(true));
                    if (btnPreset) btnPreset.addEventListener('click', () => applyPresetPadrao());
                    // já abre no preset padrão
                    applyPresetPadrao();
                } catch(e) {}
            },
            preConfirm: () => {
                let m = `*${d.nome}*\n`;
                document.querySelectorAll('.swal-copy-grid input:checked').forEach(c => {
                    m += `*${c.dataset.f}:* ${c.dataset.v}\n`;
                });
                return m;
            }
        }).then(r => {
            if (r.isConfirmed) {
                navigator.clipboard.writeText(r.value);
                Swal.fire({ icon: 'success', title: 'Copiado!', timer: 1200, showConfirmButton: false, heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
            }
        });
    };
    window.configurarLinkPublico = function(d) {
        const url = `${window.location.origin}/perfil/${d.uuid}/`;
        navigator.clipboard.writeText(url).then(() => {
            Swal.fire({ icon: 'success', title: 'Link copiado!', text: 'Link do perfil copiado.', timer: 1500, showConfirmButton: false, heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
        });
    };
    window.abrirModalReprovacaoMassa = function() {
        Swal.fire({ title:'REPROVAR', html: '<select id="m-m" class="swal2-select"><option value="fotos_ruins">Fotos Ruins</option><option value="dados_incompletos">Dados Incompletos</option><option value="perfil">Perfil Incompatível</option><option value="outros">Outros</option></select><textarea id="m-o" class="swal2-textarea"></textarea>', showCancelButton:true, confirmButtonText:'CONFIRMAR', preConfirm:()=>{return {m:document.getElementById('m-m').value, o:document.getElementById('m-o').value}} }).then(r=>{if(r.isConfirmed){
            const f=document.getElementById('changelist-form');
            f.insertAdjacentHTML('beforeend', `<input type="hidden" name="motivo_massa" value="${r.value.m}"><input type="hidden" name="obs_massa" value="${r.value.o}">`);
            document.querySelector('select[name="action"]').value='reprovar_modelos_massa'; f.submit();
        }});
    };

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Reprovação individual (popup no botão do perfil)
    window.abrirModalReprovacao = function(id, ev) {
        try { if (ev && ev.preventDefault) ev.preventDefault(); } catch(e) {}
        if (typeof Swal === 'undefined') {
            alert('SweetAlert não carregou.');
            return;
        }

        const html = `
            <div class="oc-swal-form">
                <div class="oc-swal-section">
                    <label class="oc-swal-label">Motivo</label>
                    <select id="oc-reprovar-motivo" class="swal2-select">
                        <option value="fotos_ruins">Fotos fora do padrão</option>
                        <option value="dados_incompletos">Dados incompletos/incorretos</option>
                        <option value="documentos">Documentos/infos ilegíveis</option>
                        <option value="menor_idade">Menor de idade / idade inconsistente</option>
                        <option value="perfil">Perfil não compatível no momento</option>
                        <option value="outros">Outros</option>
                    </select>
                </div>

                <div class="oc-swal-section">
                    <label class="oc-swal-label">Mensagem (opcional)</label>
                    <textarea id="oc-reprovar-obs" class="swal2-textarea" placeholder="Escreva uma orientação curta para o candidato..."></textarea>
                </div>

                <div class="oc-swal-section">
                    <label class="oc-swal-inline">
                        <input type="checkbox" id="oc-permitir-ajuste" checked>
                        <span>A pessoa pode corrigir e tentar novamente agora</span>
                    </label>

                    <div id="oc-dias-wrapper" style="display:none; margin-top:12px;">
                        <label class="oc-swal-label">Em quantos dias poderá tentar novamente?</label>
                        <input id="oc-dias" class="swal2-input" type="number" min="1" placeholder="Ex: 90">
                        <div class="oc-swal-help">Durante esse período, ao fazer login, verá quantos dias faltam.</div>
                    </div>
                </div>
            </div>
        `;

        Swal.fire({
            title: 'Reprovar / Ajuste',
            html,
            width: 'min(560px, 92vw)',
            heightAuto: false,
            scrollbarPadding: false,
            customClass: { popup: 'oc-swal-popup' },
            showCancelButton: true,
            confirmButtonText: 'CONFIRMAR',
            cancelButtonText: 'Cancelar',
            didOpen: () => {
                try {
                    const popup = Swal.getPopup();
                    if (popup) popup.style.overflowX = 'hidden';
                    const htmlContainer = Swal.getHtmlContainer();
                    if (htmlContainer) htmlContainer.style.overflowX = 'hidden';
                } catch(e) {}
                const chk = document.getElementById('oc-permitir-ajuste');
                const wrap = document.getElementById('oc-dias-wrapper');
                const sync = () => {
                    const allow = chk && chk.checked;
                    if (wrap) wrap.style.display = allow ? 'none' : 'block';
                };
                if (chk) chk.addEventListener('change', sync);
                sync();
            },
            preConfirm: () => {
                const motivo = (document.getElementById('oc-reprovar-motivo') || {}).value || 'outros';
                const observacao = (document.getElementById('oc-reprovar-obs') || {}).value || '';
                const permitir_ajuste = !!(document.getElementById('oc-permitir-ajuste') || {}).checked;
                const dias_bloqueio = (document.getElementById('oc-dias') || {}).value || '';

                if (!permitir_ajuste) {
                    const n = parseInt(dias_bloqueio, 10);
                    if (!n || n < 1) {
                        Swal.showValidationMessage('Informe em quantos dias poderá tentar novamente.');
                        return false;
                    }
                }

                return { motivo, observacao, permitir_ajuste, dias_bloqueio };
            }
        }).then(async (r) => {
            if (!r.isConfirmed) return;
            const payload = r.value || {};

            try {
                const fd = new FormData();
                fd.append('motivo', payload.motivo || 'outros');
                fd.append('observacao', payload.observacao || '');
                fd.append('permitir_ajuste', payload.permitir_ajuste ? '1' : '0');
                if (!payload.permitir_ajuste) fd.append('dias_bloqueio', payload.dias_bloqueio || '');

                const res = await fetch(`/admin/core/userprofile/${id}/reprovar/`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken') || ''
                    },
                    body: fd
                });

                if (!res.ok) throw new Error('Falha ao reprovar');
                const data = await res.json();
                if (data && data.ok) {
                    Swal.fire({ icon: 'success', title: 'Atualizado!', timer: 1200, showConfirmButton: false })
                        .then(() => window.location.reload());
                } else {
                    throw new Error('Resposta inválida');
                }
            } catch (e) {
                console.error(e);
                Swal.fire({ icon: 'error', title: 'Erro', text: 'Não foi possível concluir a reprovação.', heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
            }
        });
    };

    async function postAdminAction(url) {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken') || ''
            }
        });
        if (!res.ok) throw new Error('Falha na ação');
        return await res.json();
    }

    // Voltar perfil aprovado para análise
    window.voltarParaAnalise = function(id) {
        Swal.fire({
            title: 'Voltar para análise?',
            text: 'O cadastro voltará para PENDENTE.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'SIM, VOLTAR',
            cancelButtonText: 'Cancelar',
            heightAuto: false,
            customClass: { popup: 'oc-swal-popup' }
        }).then(async r => {
            if (!r.isConfirmed) return;
            try {
                const data = await postAdminAction(`/admin/core/userprofile/${id}/voltar-analise/`);
                if (data && data.ok) {
                    Swal.fire({ icon: 'success', title: 'Atualizado!', timer: 1000, showConfirmButton: false, heightAuto: false, customClass: { popup: 'oc-swal-popup' } })
                        .then(() => window.location.reload());
                } else {
                    throw new Error('Resposta inválida');
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Erro', text: 'Não foi possível voltar para análise.', heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
            }
        });
    };

    // Excluir cadastro
    window.excluirCadastro = function(id) {
        Swal.fire({
            title: 'Excluir cadastro?',
            text: 'Essa ação é permanente.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'SIM, EXCLUIR',
            cancelButtonText: 'Cancelar',
            heightAuto: false,
            customClass: { popup: 'oc-swal-popup' }
        }).then(async r => {
            if (!r.isConfirmed) return;
            try {
                const data = await postAdminAction(`/admin/core/userprofile/${id}/excluir/`);
                if (data && data.ok) {
                    window.location.href = '/admin/core/userprofile/';
                } else {
                    throw new Error('Resposta inválida');
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Erro', text: 'Não foi possível excluir.', heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
            }
        });
    };

    // Excluir e banir CPF
    window.excluirEBanirCPF = function(id) {
        Swal.fire({
            title: 'Excluir e banir CPF?',
            html: '<div style="text-align:left;">Isso exclui o cadastro e impede novo cadastro com o mesmo CPF.</div>',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'SIM, BANIR',
            cancelButtonText: 'Cancelar',
            heightAuto: false,
            customClass: { popup: 'oc-swal-popup' }
        }).then(async r => {
            if (!r.isConfirmed) return;
            try {
                const data = await postAdminAction(`/admin/core/userprofile/${id}/banir-cpf/`);
                if (data && data.ok) {
                    window.location.href = '/admin/core/userprofile/';
                } else {
                    throw new Error('Resposta inválida');
                }
            } catch (e) {
                Swal.fire({ icon: 'error', title: 'Erro', text: 'Não foi possível banir CPF.', heightAuto: false, customClass: { popup: 'oc-swal-popup' } });
            }
        });
    };

    // --- LOOP (sem spam no console) ---
    // Evita criar múltiplos intervals caso o JS seja injetado duas vezes.
    if (window.__opencasting_admin_custom_interval) {
        clearInterval(window.__opencasting_admin_custom_interval);
    }
    let setupCount = 0;
    window.__opencasting_admin_custom_interval = setInterval(() => {
        setupCount++;
        setupUI();
        // Sidebar só é construída quando o usuário clica em "Filtros" (openCastingFilters)
        // mas deixamos um fallback seguro para a primeira carga.
        if(!isSidebarBuilt) {
            // não cria a sidebar automaticamente para não aparecer “vazia”
        }
        if(setupCount > 40) {
            clearInterval(window.__opencasting_admin_custom_interval);
        }
    }, CHECK_INTERVAL);

})();