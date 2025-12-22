/**
 * OPENCASTING CRM - GESTOR V15 (SEQUENCIAL & COMPLETO)
 * ------------------------------------------------------------------
 * 1. VISIBILIDADE: Filtros nativos carregam visíveis (para o JS ler).
 * 2. CLONAGEM: JS copia para a sidebar.
 * 3. LIMPEZA: JS esconde os originais da tela principal.
 * 4. TOOLS: WhatsApp, Link Cliente e Reprovação em Massa.
 */

(function() {
    'use strict';

    const CHECK_INTERVAL = 300;
    let isSidebarBuilt = false;
    let searchDebounceTimer = null;

    // Garante SweetAlert2
    if (typeof Swal === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
        document.head.appendChild(script);
    }

    // ============================================================
    // 1. FUNÇÕES GLOBAIS (ACESSÍVEIS PELOS BOTÕES HTML)
    // ============================================================

    // Abertura da Sidebar
    window.openCastingFilters = function() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        const backdrop = document.getElementById('filter-backdrop');
        if (sidebar && backdrop) {
            sidebar.classList.add('active');
            backdrop.style.display = 'block';
        } else {
            console.log("Forçando construção da Sidebar...");
            buildFilterSidebar();
            setTimeout(() => window.openCastingFilters(), 150);
        }
    };

    window.closeSidebar = function() {
        const sidebar = document.getElementById('custom-sidebar-filter');
        const backdrop = document.getElementById('filter-backdrop');
        if(sidebar) sidebar.classList.remove('active');
        if(backdrop) backdrop.style.display = 'none';
    };

    // Auxiliar: Checkbox "Selecionar Tudo" no Popup
    window.selecionarTudo = (status) => { 
        document.querySelectorAll('.swal-copy-grid input[type="checkbox"]').forEach(c => c.checked = status); 
    };
    
    // HTML do Popup de Seleção
    function gerarCheckboxesPopUp(dados) {
        return `
            <div style="text-align: left; font-family: sans-serif;">
                <div style="margin-bottom: 20px; display: flex; gap: 10px;">
                    <button type="button" class="swal2-confirm swal2-styled" style="background:#444; font-size: 0.7rem; padding: 8px 12px;" onclick="selecionarTudo(true)">TUDO</button>
                    <button type="button" class="swal2-confirm swal2-styled" style="background:#009688; font-size: 0.7rem; padding: 8px 12px;" onclick="selecionarTudo(false)">LIMPAR</button>
                </div>
                <div class="swal-copy-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-height: 400px; overflow-y: auto; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                    <div class="cp-item"><input type="checkbox" id="cp-nome" data-field="Nome" data-val="${dados.nome}" checked> <label for="cp-nome">Nome</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-idade" data-field="Idade" data-val="${dados.idade}" checked> <label for="cp-idade">Idade</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-zap" data-field="WhatsApp" data-val="${dados.whatsapp}"> <label for="cp-zap">WhatsApp</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-altura" data-field="Altura" data-val="${dados.altura}m"> <label for="cp-altura">Altura</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-peso" data-field="Peso" data-val="${dados.peso}kg"> <label for="cp-peso">Peso</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-manequim" data-field="Manequim" data-val="${dados.manequim}"> <label for="cp-manequim">Manequim</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-calcado" data-field="Calçado" data-val="${dados.calcado}"> <label for="cp-calcado">Calçado</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-pix" data-field="PIX" data-val="${dados.pix}"> <label for="cp-pix">PIX</label></div>
                </div>
            </div>
        `;
    }

    // Ação: Copiar WhatsApp
    window.copiarInformacoesPerfil = function(dados) {
        Swal.fire({
            title: 'ENVIAR WHATSAPP',
            html: gerarCheckboxesPopUp(dados),
            showCancelButton: true,
            confirmButtonText: 'COPIAR TEXTO',
            confirmButtonColor: '#25D366',
            preConfirm: () => {
                let msg = `*APRESENTAÇÃO ${dados.nome}*\n\n`;
                const checks = document.querySelectorAll('.swal-copy-grid input[type="checkbox"]:checked');
                if (!checks.length) return Swal.showValidationMessage('Selecione ao menos um dado!');
                checks.forEach(c => { msg += `*${c.getAttribute('data-field')}:* ${c.getAttribute('data-val')}\n`; });
                return msg;
            }
        }).then((res) => { 
            if (res.isConfirmed) { 
                navigator.clipboard.writeText(res.value); 
                Swal.fire({ icon:'success', title:'Copiado!', timer:1500, showConfirmButton:false }); 
            } 
        });
    };

    // Ação: Gerar Link Público
    window.configurarLinkPublico = function(dados) {
        Swal.fire({
            title: 'GERAR LINK CLIENTE',
            html: gerarCheckboxesPopUp(dados),
            showCancelButton: true,
            confirmButtonText: 'GERAR LINK',
            confirmButtonColor: '#3498db',
            preConfirm: () => {
                const checks = document.querySelectorAll('.swal-copy-grid input[type="checkbox"]:checked');
                if (!checks.length) return Swal.showValidationMessage('Selecione campos!');
                const sel = Array.from(checks).map(c => c.id.replace('cp-', '')).join(',');
                return `${window.location.origin}/perfil/${dados.uuid}/?show=${sel}`;
            }
        }).then((res) => { 
            if (res.isConfirmed) { 
                navigator.clipboard.writeText(res.value); 
                Swal.fire({ icon:'success', title:'Link Copiado!', timer:1500, showConfirmButton:false }); 
            } 
        });
    };

    // Ação: Reprovação em Massa
    window.abrirModalReprovacaoMassa = function() {
        Swal.fire({
            title: 'REPROVAR SELECIONADOS',
            html: `
                <div style="text-align: left;">
                    <label style="font-weight:bold;">Motivo:</label>
                    <select id="m-motivo" class="swal2-select" style="width:100%;">
                        <option value="fotos_ruins">Fotos Ruins / Escuras</option>
                        <option value="dados_incompletos">Dados Incompletos</option>
                        <option value="perfil">Perfil não compatível</option>
                        <option value="outros">Outros</option>
                    </select>
                    <label style="font-weight:bold; margin-top:10px; display:block;">Obs (Mensagem pro modelo):</label>
                    <textarea id="m-obs" class="swal2-textarea" placeholder="Descreva o que precisa ser ajustado..."></textarea>
                </div>
            `,
            showCancelButton: true,
            confirmButtonColor: '#c0392b',
            confirmButtonText: 'CONFIRMAR REPROVAÇÃO',
            preConfirm: () => { 
                return { m: document.getElementById('m-motivo').value, o: document.getElementById('m-obs').value }; 
            }
        }).then((res) => {
            if (res.isConfirmed) {
                const f = document.getElementById('changelist-form');
                let i1 = document.createElement('input'); i1.type='hidden'; i1.name='motivo_massa'; i1.value=res.value.m;
                let i2 = document.createElement('input'); i2.type='hidden'; i2.name='obs_massa'; i2.value=res.value.o;
                f.appendChild(i1); f.appendChild(i2);
                document.querySelector('select[name="action"]').value = 'reprovar_modelos_massa';
                f.submit();
            }
        });
    };

    // ============================================================
    // 2. CONSTRUTOR DA SIDEBAR (SCANNER SEQUENCIAL)
    // ============================================================
    function buildFilterSidebar() {
        if (document.getElementById('custom-sidebar-filter')) return;

        // 1. Cria Estrutura
        const sidebar = document.createElement('div');
        sidebar.id = 'custom-sidebar-filter';
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <h3>FILTROS DA AGÊNCIA</h3>
                <button type="button" id="btn-close-sidebar">&times;</button>
            </div>
            <div id="sidebar-content">
                <div class="range-section">
                    <div class="filter-group-box"><label>Idade (Anos)</label><div class="range-inputs"><input type="number" id="f-idade-min" placeholder="Min"><span>até</span><input type="number" id="f-idade-max" placeholder="Max"></div></div>
                    <div class="filter-group-box"><label>Peso (KG)</label><div class="range-inputs"><input type="number" id="f-peso-min" placeholder="Min"><span>até</span><input type="number" id="f-peso-max" placeholder="Max"></div></div>
                    <div class="filter-group-box"><label>Altura (M)</label><div class="range-inputs"><input type="text" id="f-altura-min" placeholder="1.60"><span>até</span><input type="text" id="f-altura-max" placeholder="1.95"></div></div>
                    <div class="filter-group-box"><label>Sapato</label><div class="range-inputs"><input type="number" id="f-sapato-min" placeholder="34"><span>até</span><input type="number" id="f-sapato-max" placeholder="44"></div></div>
                </div>
                <hr style="margin: 20px 0; border-top: 1px solid #eee;">
                
                <div id="django-filters-target"></div>

                <div style="padding: 20px 0;">
                    <button type="button" id="btn-apply-advanced">APLICAR FILTROS AGORA</button>
                    <a href="." class="btn-clear-all" style="display:block; text-align:center; margin-top:15px; font-weight:bold; color:#f39c12; font-size:11px; text-decoration:none;">LIMPAR TUDO</a>
                </div>
            </div>
        `;
        document.body.appendChild(sidebar);

        const backdrop = document.createElement('div');
        backdrop.id = 'filter-backdrop';
        document.body.appendChild(backdrop);

        document.getElementById('btn-close-sidebar').onclick = window.closeSidebar;
        backdrop.onclick = window.closeSidebar;

        // Recupera valores da URL
        const p = new URLSearchParams(window.location.search);
        ['idade', 'peso', 'altura', 'sapato'].forEach(key => {
            if(p.get(key+'_min')) document.getElementById('f-'+key+'-min').value = p.get(key+'_min');
            if(p.get(key+'_max')) document.getElementById('f-'+key+'-max').value = p.get(key+'_max');
        });

        // 2. SCANNER SEQUENCIAL
        const target = document.getElementById('django-filters-target');
        const containers = [
            document.getElementById('changelist-filter'),
            document.querySelector('.jazzmin-sidebar-filter'),
            document.querySelector('#jazzy-filters')
        ];

        let foundSource = false;

        containers.forEach(div => {
            if (div && !foundSource) {
                // Verifica se tem conteúdo
                const items = div.querySelectorAll('h3, ul, details');
                if (items.length > 0) {
                    foundSource = true;
                    
                    // Copia os itens
                    items.forEach(el => {
                        const txt = el.innerText.toLowerCase();
                        if (txt.includes('idade m') || txt.includes('peso m') || txt.includes('altura m') || txt.includes('sapato m')) return;
                        
                        const clone = el.cloneNode(true);
                        
                        // Estilos
                        if (clone.tagName === 'H3') {
                            clone.style.fontSize = '0.75rem'; clone.style.fontWeight = '800'; 
                            clone.style.marginTop = '15px'; clone.style.color = '#555'; 
                            clone.style.textTransform = 'uppercase';
                        }
                        if (clone.tagName === 'UL') {
                            clone.style.paddingLeft = '0'; clone.style.listStyle = 'none';
                            clone.querySelectorAll('li a').forEach(a => {
                                a.style.display = 'block'; a.style.padding = '4px 0'; a.style.color = '#666';
                                if (a.parentElement.classList.contains('selected')) { a.style.color = '#009688'; a.style.fontWeight = 'bold'; }
                            });
                        }
                        if (clone.tagName === 'DETAILS') { clone.open = true; clone.style.width = '100%'; }
                        
                        target.appendChild(clone);
                    });

                    // IMPORTANTE: Esconde o original AGORA, depois de copiar
                    div.style.display = 'none';
                }
            }
        });

        if (!foundSource) {
            target.innerHTML = "<p style='text-align:center; color:#999; font-size:12px; margin-top:20px;'>Filtros nativos não detectados.<br>O Django gerou eles?</p>";
        }

        // Botão Aplicar
        document.getElementById('btn-apply-advanced').onclick = function() {
            const params = new URLSearchParams(window.location.search);
            ['idade', 'peso', 'altura', 'sapato'].forEach(key => {
                const min = document.getElementById('f-'+key+'-min').value;
                const max = document.getElementById('f-'+key+'-max').value;
                if(min) params.set(key+'_min', min); else params.delete(key+'_min');
                if(max) params.set(key+'_max', max); else params.delete(key+'_max');
            });
            params.delete('p');
            window.location.search = params.toString();
        };

        isSidebarBuilt = true;
    }

    // ============================================================
    // 3. UI: TOOLBAR, BUSCA E HOVER
    // ============================================================
    function setupUI() {
        // Fix Hover
        document.querySelectorAll('.btn-group-custom').forEach(g => {
            const d = g.querySelector('.dropdown-content');
            if(d) { g.onmouseenter = () => d.style.display='block'; g.onmouseleave = () => d.style.display='none'; }
        });

        // Toolbar
        if (!document.getElementById('custom-filter-toolbar')) {
            const form = document.getElementById('changelist-form');
            if (form) {
                const toolbar = document.createElement('div');
                toolbar.id = 'custom-filter-toolbar';
                toolbar.innerHTML = `
                    <div class="toolbar-search-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" id="toolbar-search-input" placeholder="Pesquisar...">
                    </div>
                    <div class="toolbar-actions">
                        <button type="button" onclick="window.openCastingFilters()" id="btn-trigger-filter">
                            <i class="fas fa-filter"></i> FILTRAGEM AVANÇADA
                        </button>
                    </div>
                `;
                form.parentNode.insertBefore(toolbar, form);
                
                // Busca Real-time
                const inp = document.getElementById('toolbar-search-input');
                const p = new URLSearchParams(window.location.search);
                if(p.get('q')) inp.value = p.get('q');
                
                inp.oninput = (e) => {
                    clearTimeout(searchDebounceTimer);
                    searchDebounceTimer = setTimeout(() => {
                        const pp = new URLSearchParams(window.location.search);
                        if(e.target.value) pp.set('q', e.target.value); else pp.delete('q');
                        pp.delete('p');
                        window.location.search = pp.toString();
                    }, 800);
                };

                // Botões de Ação
                const actDiv = document.querySelector('.actions');
                const actSel = document.querySelector('select[name="action"]');
                if (actDiv && actSel) {
                    actSel.style.display = 'none';
                    const grp = document.createElement('div');
                    grp.className = 'custom-action-buttons';
                    grp.innerHTML = '<span style="font-weight:900; color:#009688; margin-right:15px; font-size:11px;">AÇÕES:</span>';
                    Array.from(actSel.options).forEach(o => {
                        if (!o.value) return;
                        const b = document.createElement('button'); b.type = 'button'; b.className = 'action-btn-custom';
                        const txt = o.text.toLowerCase();
                        if (txt.includes('aprov')) { b.innerHTML = '<i class="fas fa-check"></i> APROVAR'; b.classList.add('btn-act-approve'); }
                        else if (txt.includes('reprov')) { b.innerHTML = '<i class="fas fa-times"></i> REPROVAR'; b.classList.add('btn-act-reject'); }
                        else if (txt.includes('excluir')) { b.innerHTML = '<i class="fas fa-trash"></i> EXCLUIR'; b.classList.add('btn-act-delete'); }
                        else { b.innerText = o.text.toUpperCase(); }
                        b.onclick = () => {
                            if (txt.includes('reprov')) window.abrirModalReprovacaoMassa();
                            else { if (txt.includes('excluir') && !confirm('Tem certeza?')) return; actSel.value = o.value; form.submit(); }
                        };
                        grp.appendChild(b);
                    });
                    actDiv.appendChild(grp);
                    const toggleBtns = () => { grp.style.display = document.querySelectorAll('.action-select:checked').length > 0 ? 'flex' : 'none'; };
                    document.body.addEventListener('change', toggleBtns);
                    toggleBtns();
                }
            }
        }
    }

    // Loop
    setInterval(() => {
        setupUI();
        if(!isSidebarBuilt) buildFilterSidebar();
    }, CHECK_INTERVAL);

})();