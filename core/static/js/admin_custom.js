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
    function buildFilterSidebar() {
        if (document.getElementById('custom-sidebar-filter')) return;

        // 1. ESTRUTURA
        const sidebar = document.createElement('div');
        sidebar.id = 'custom-sidebar-filter';
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <h3>FILTROS DA AGÊNCIA</h3>
                <button type="button" id="btn-close-sidebar">&times;</button>
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

        document.getElementById('btn-close-sidebar').onclick = window.closeSidebar;
        backdrop.onclick = window.closeSidebar;

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
                if (selectCount >= 3) return node;
                node = node.parentElement;
            }
        }

        // Fallback: acha um botão/submit com texto PESQUISAR fora da sidebar e sobe até um container com muitos selects
        const searchButtons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'))
            .filter(b => {
                if (!b) return false;
                if (b.closest && b.closest('#custom-sidebar-filter')) return false;
                const txt = ((b.innerText || b.value || '') + '').toLowerCase();
                return txt.includes('pesquisar');
            });

        let best = null;
        let bestScore = 0;
        for (const btn of searchButtons) {
            let node = btn.parentElement;
            let guard = 0;
            while (node && guard++ < 14) {
                if (node.closest && node.closest('#custom-sidebar-filter')) break;
                const selects = node.querySelectorAll ? Array.from(node.querySelectorAll('select')).filter(s => s && s.name !== 'action').length : 0;
                if (selects >= 3) {
                    const score = selects * 10 + 100;
                    if (score > bestScore) {
                        bestScore = score;
                        best = node;
                    }
                }
                node = node.parentElement;
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

        // Não depende de visibilidade: o painel pode estar oculto pela classe oc-main-filters-hidden
        const best = findMainFilterPanelContainer();
        if (!best) return false;

        // Move o painel para a sidebar
        const wrapper = document.createElement('div');
        wrapper.className = 'filter-group-box oc-moved-main-filters';
        const label = document.createElement('label');
        label.innerText = 'Filtros';
        wrapper.appendChild(label);

        // Marca o painel original para estilização dentro da sidebar (sem esconder)
        try {
            best.classList.add('oc-main-filters-panel');
            best.classList.remove('oc-main-filters-hidden');
        } catch(e){}
        wrapper.appendChild(best);
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
        ensureDjangoActionsCounter();

        // Marca contexto da página para CSS responsivo (PythonAnywhere/mobile)
        try {
            const path = (window.location && window.location.pathname) ? window.location.pathname : '';
            if (document.body && document.body.classList) {
                if (path.includes('/admin/core/userprofile/') && document.body.classList.contains('change-list')) {
                    document.body.classList.add('oc-userprofile-changelist');
                }
            }
        } catch(e) {}

        // Cria o botão "Filtros" se ainda não existir
        if (!document.getElementById('custom-filter-toolbar')) {
            const form = document.getElementById('changelist-form');
            if (form) {
                const toolbar = document.createElement('div');
                toolbar.id = 'custom-filter-toolbar';
                toolbar.innerHTML = `
                    <div class="toolbar-actions">
                        <input id="oc-live-search" type="search" placeholder="Pesquisar (nome, CPF, WhatsApp...)" autocomplete="off" />
                        <button type="button" id="btn-open-sidebar" class="btn-filtros-avancados">Filtros</button>
                    </div>
                `;
                form.parentNode.insertBefore(toolbar, form);
                const btn = document.getElementById('btn-open-sidebar');
                if (btn) btn.addEventListener('click', () => window.openCastingFilters());
            }
        }

        // garante o live-search mesmo se o toolbar já existia
        ensureLiveSearchInput();

        // Mobile: usa bolinha colorida no lugar do texto do status
        applyUserProfileStatusDotForMobile();

        // Hover Menus
        document.querySelectorAll('.btn-group-custom').forEach(g => {
            const d = g.querySelector('.dropdown-content');
            if(d) { g.onmouseenter = () => d.style.display='block'; g.onmouseleave = () => d.style.display='none'; }
        });

        // Garante que o painel do topo fique oculto SEMPRE (inclusive após clicar em PESQUISAR e recarregar)
        try { hideMainFilterPanel(); } catch(e){}
    }

    // --- FERRAMENTAS EXTRAS ---
    window.selecionarTudo = (s) => document.querySelectorAll('.swal-copy-grid input').forEach(c => c.checked = s);
    function checkHtml(d) {
        return `<div class="swal-copy-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;text-align:left;">
        <div class="cp-item"><input type="checkbox" data-f="Nome" data-v="${d.nome}" checked> Nome</div>
        <div class="cp-item"><input type="checkbox" data-f="Zap" data-v="${d.whatsapp}"> Zap</div>
        <div class="cp-item"><input type="checkbox" data-f="Altura" data-v="${d.altura}m"> Altura</div>
        <div class="cp-item"><input type="checkbox" data-f="Peso" data-v="${d.peso}kg"> Peso</div></div>`;
    }
    window.copiarInformacoesPerfil = function(d) {
        Swal.fire({ title:'WHATSAPP', html: checkHtml(d), showCancelButton:true, confirmButtonText:'COPIAR', preConfirm:()=>{
            let m=`*${d.nome}*\n`; document.querySelectorAll('.swal-copy-grid input:checked').forEach(c=>{m+=`*${c.dataset.f}:* ${c.dataset.v}\n`}); return m;
        }}).then(r=>{if(r.isConfirmed){navigator.clipboard.writeText(r.value);Swal.fire('Copiado!');}});
    };
    window.configurarLinkPublico = function(d) {
        Swal.fire({ title:'LINK', html: checkHtml(d), showCancelButton:true, confirmButtonText:'GERAR', preConfirm:()=>{return `${window.location.origin}/perfil/${d.uuid}/`;}}).then(r=>{if(r.isConfirmed){navigator.clipboard.writeText(r.value);Swal.fire('Copiado!');}});
    };
    window.abrirModalReprovacaoMassa = function() {
        Swal.fire({ title:'REPROVAR', html: '<select id="m-m" class="swal2-select"><option value="fotos_ruins">Fotos Ruins</option><option value="dados_incompletos">Dados Incompletos</option><option value="perfil">Perfil Incompatível</option><option value="outros">Outros</option></select><textarea id="m-o" class="swal2-textarea"></textarea>', showCancelButton:true, confirmButtonText:'CONFIRMAR', preConfirm:()=>{return {m:document.getElementById('m-m').value, o:document.getElementById('m-o').value}} }).then(r=>{if(r.isConfirmed){
            const f=document.getElementById('changelist-form');
            f.insertAdjacentHTML('beforeend', `<input type="hidden" name="motivo_massa" value="${r.value.m}"><input type="hidden" name="obs_massa" value="${r.value.o}">`);
            document.querySelector('select[name="action"]').value='reprovar_modelos_massa'; f.submit();
        }});
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