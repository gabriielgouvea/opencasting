(function() {
    'use strict';

    // Configurações Globais
    const log = (msg) => console.log("%cOpenCasting: " + msg, "color: #009688; font-weight: bold;");
    const CHECK_INTERVAL = 500;
    const MAX_ATTEMPTS = 20;
    let attemptCount = 0;
    let searchDebounce = null;

    // ============================================================
    // 1. FUNÇÕES AUXILIARES (MODAIS, MÁSCARAS)
    // ============================================================

    // Modal de Reprovação
    window.abrirModalReprovacao = function(id) {
        const old = document.getElementById('modal-reprovacao');
        if(old) old.remove();

        const modal = document.createElement('div');
        modal.id = 'modal-reprovacao';
        modal.className = 'custom-modal-overlay';
        modal.innerHTML = `
            <div class="custom-modal-box">
                <div class="modal-header">
                    <h3><i class="fas fa-times-circle"></i> REPROVAR</h3>
                    <button onclick="document.getElementById('modal-reprovacao').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Motivo da reprovação:</p>
                    <textarea id="motivo-reprovacao" placeholder="Digite o motivo..."></textarea>
                </div>
                <div class="modal-footer">
                    <button class="btn-cancel" onclick="document.getElementById('modal-reprovacao').remove()">CANCELAR</button>
                    <button class="btn-confirm" onclick="confirmarReprovacao(${id})">CONFIRMAR</button>
                </div>
            </div>`;
        document.body.appendChild(modal);
        setTimeout(() => document.getElementById('motivo-reprovacao').focus(), 100);
    };

    window.confirmarReprovacao = function(id) {
        const m = document.getElementById('motivo-reprovacao').value;
        if(!m.trim()) { alert("Motivo obrigatório"); return; }
        window.location.href = `/admin/core/userprofile/${id}/reprovar/?motivo=${encodeURIComponent(m)}`;
    };

    // Máscara de Altura (170 -> 1.70)
    function applyHeightMask(e) {
        let v = e.target.value.replace(/\D/g, "");
        if (v.length > 3) v = v.slice(0, 3);
        if (v.length >= 2) v = v.slice(0, 1) + "." + v.slice(1);
        e.target.value = v;
    }

    // ============================================================
    // 2. MODO DETALHE (PERFIL DO CANDIDATO)
    // ============================================================
    function initDetailView() {
        // Verifica se está na tela de edição
        const row = document.querySelector('.submit-row');
        if (!row || document.querySelector('.sidebar-custom-actions')) return;

        // Pega o painel criado no admin.py
        const panel = document.querySelector('.field-painel_acoes .readonly');
        
        if (panel) {
            const sb = document.createElement('div');
            sb.className = 'sidebar-custom-actions';
            
            // Clona o conteúdo para manipular
            const tmp = document.createElement('div');
            tmp.innerHTML = panel.innerHTML;
            
            // Move Status
            const bdg = tmp.querySelector('.status-badge');
            if(bdg) {
                bdg.className = bdg.className.replace('status-', 'sidebar-status-badge badge-');
                sb.appendChild(bdg);
            }

            // Move Botões
            tmp.querySelectorAll('a, button').forEach(b => {
                b.classList.remove('btn-action');
                b.classList.add('sidebar-btn');
                
                // Aplica classes de cor
                if(b.className.includes('approve')) b.classList.add('sb-approve');
                else if(b.className.includes('reject')) b.classList.add('sb-reject');
                else if(b.className.includes('whatsapp')) b.classList.add('sb-whatsapp');
                else if(b.className.includes('email')) b.classList.add('sb-email');
                else if(b.className.includes('password')) b.classList.add('sb-password');
                else b.classList.add('sb-reconsider');
                
                sb.appendChild(b);
            });
            
            // Insere na barra lateral direita
            row.appendChild(sb);
        }
    }

    // ============================================================
    // 3. MODO LISTA (TABELA DE PROMOTORES)
    // ============================================================
    function initListView() {
        const lst = document.getElementById('changelist');
        if (!lst || document.getElementById('custom-filter-toolbar')) return;

        log("Construindo Interface de Lista...");

        // --- 3.1 GAVETA LATERAL (SIDEBAR) ---
        const sb = document.createElement('div');
        sb.id = 'custom-sidebar-filter';
        sb.innerHTML = `
            <div class="sidebar-header"><h3>FILTROS</h3><button id="btn-close-filter">&times;</button></div>
            <div id="sidebar-content">
                <div class="filter-group-box"><label>FAIXA ETÁRIA</label><div class="range-inputs"><input type="number" id="custom_idade_min" placeholder="De"><input type="number" id="custom_idade_max" placeholder="Até"></div></div>
                <div class="filter-group-box"><label>ALTURA</label><div class="range-inputs"><input type="text" id="custom_altura_min" placeholder="1.60"><input type="text" id="custom_altura_max" placeholder="1.80"></div></div>
                <div class="filter-group-box"><label>MANEQUIM</label><div class="range-inputs"><input type="number" id="custom_manequim_min"><input type="number" id="custom_manequim_max"></div></div>
                <div class="filter-group-box"><label>CALÇADO</label><div class="range-inputs"><input type="number" id="custom_calcado_min"><input type="number" id="custom_calcado_max"></div></div>
                <div class="filter-group-box"><label>CAMISETA</label><div class="range-inputs">
                    <select id="custom_camiseta_min"><option value="">De...</option><option value="PP">PP</option><option value="P">P</option><option value="M">M</option><option value="G">G</option><option value="GG">GG</option></select>
                    <select id="custom_camiseta_max"><option value="">Até...</option><option value="PP">PP</option><option value="P">P</option><option value="M">M</option><option value="G">G</option><option value="GG">GG</option></select>
                </div></div>
                
                <hr style="border-top:1px solid #ddd; margin:15px 0;">
                
                <div id="original-filters-place"></div>
                
                <button id="btn-realizar-busca">APLICAR FILTROS</button>
            </div>`;
        document.body.appendChild(sb);
        
        sb.querySelector('#custom_altura_min').addEventListener('input', applyHeightMask);
        sb.querySelector('#custom_altura_max').addEventListener('input', applyHeightMask);

        const bd = document.createElement('div'); bd.id = 'filter-backdrop'; document.body.appendChild(bd);

        // --- 3.2 TOOLBAR (BUSCA E BOTÃO) ---
        const tb = document.createElement('div'); tb.id = 'custom-filter-toolbar';
        tb.innerHTML = `
            <div class="toolbar-search-container"><i class="fas fa-search search-icon"></i><input type="text" id="toolbar-search-input" placeholder="Buscar..." autocomplete="off"></div>
            <div class="toolbar-actions"><button id="btn-open-filter"><i class="fas fa-filter"></i> FILTROS</button></div>
        `;
        const frm = document.getElementById('changelist-form');
        if(frm) frm.parentNode.insertBefore(tb, frm);

        // --- 3.3 LÓGICA DE INTERAÇÃO ---
        const toggle = (e) => { if(e)e.preventDefault(); sb.classList.toggle('active'); bd.style.display = sb.classList.contains('active')?'block':'none'; };
        document.getElementById('btn-open-filter').onclick = toggle;
        document.getElementById('btn-close-filter').onclick = toggle;
        bd.onclick = toggle;

        // Botão Limpar (Detecta se tem filtros ativos)
        const p = new URLSearchParams(window.location.search);
        // Lista expandida de chaves para detectar filtro ativo
        const keys = [
            'q','idade_min','idade_max','altura_min','altura_max','manequim_min','manequim_max',
            'calcado_min','calcado_max','camiseta_min','camiseta_max',
            'status','genero','etnia','nacionalidade','is_pcd','cabelo_tipo','cabelo_comprimento',
            'olhos','experiencia','disponibilidade','area_atuacao','nivel_ingles','nivel_espanhol','nivel_frances'
        ];
        let has = false; 
        p.forEach((v,k)=>{ if((k!=='o'&&k!=='ot'&&k!=='e'&&v)||keys.some(x=>k.includes(x))) has=true; });
        
        if(has) { 
            const clr = document.createElement('a'); clr.href=window.location.pathname; 
            clr.className='btn-limpar-custom'; clr.innerHTML='<i class="fas fa-times"></i> LIMPAR'; 
            tb.querySelector('.toolbar-actions').prepend(clr); 
        }

        // Live Search
        const inp = document.getElementById('toolbar-search-input');
        if(p.get('q')) inp.value = p.get('q');
        inp.addEventListener('input', () => {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(() => {
                const np = new URLSearchParams(window.location.search);
                if(inp.value.trim()) np.set('q',inp.value.trim()); else np.delete('q');
                np.delete('p'); window.location.search = np.toString();
            }, 1000);
        });

        // --- 3.4 MOVER FILTROS (FIX JAZZMIN/SELECT2) ---
        const tgt = document.getElementById('original-filters-place');
        
        // Busca TODOS os selects da página (exceto Action e os Manuais)
        const allSelects = document.querySelectorAll('select:not([name="action"]):not([id^="custom_"])');
        
        allSelects.forEach(s => {
            // Se ainda não foi movido
            if(!tgt.contains(s)) {
                const wrap = document.createElement('div'); 
                wrap.className = 'filter-group-box';
                
                // Tenta achar o label
                let lbl = s.name.toUpperCase().replace(/_/g, ' ');
                if(s.previousElementSibling && s.previousElementSibling.tagName==='LABEL') lbl = s.previousElementSibling.innerText;
                
                // === A MÁGICA ACONTECE AQUI ===
                // Remove classes que escondem o select (Select2, Jazzmin hidden classes)
                s.classList.remove('select2-hidden-accessible', 'form-control', 'admin-autocomplete');
                // Força propriedades CSS para torná-lo visível e normal
                s.style.display = 'block';
                s.style.visibility = 'visible';
                s.style.width = '100%';
                s.style.height = '38px';
                s.style.opacity = '1';
                s.style.appearance = 'auto'; // Restaura aparência padrão do navegador
                s.removeAttribute('hidden');
                s.removeAttribute('aria-hidden');
                s.removeAttribute('tabindex'); // Remove controle de tabulação do select2
                
                // Cria label e move
                const l = document.createElement('label'); l.innerText = lbl.replace(/:/g,'');
                wrap.appendChild(l);
                wrap.appendChild(s);
                tgt.appendChild(wrap);
            }
        });
        
        // Esconde os containers originais que ficaram vazios ou quebrados
        // Jazzmin geralmente usa .card ou .filter-wrapper
        const leftovers = document.querySelectorAll('#changelist-form .card, #changelist-filter, .filter-wrapper');
        leftovers.forEach(c => { 
            // Se o card não tem tabela dentro, esconde
            if(!c.querySelector('table')) c.style.display='none'; 
        });


        // --- 3.5 BOTÃO APLICAR ---
        document.getElementById('btn-realizar-busca').onclick = () => {
            const np = new URLSearchParams(window.location.search);
            // Função helper para pegar valor
            const set = (id,k)=>{ const e=document.getElementById(id); if(e&&e.value) np.set(k,e.value); else np.delete(k); };
            
            // Pega manuais
            set('custom_idade_min','idade_min'); set('custom_idade_max','idade_max');
            set('custom_altura_min','altura_min'); set('custom_altura_max','altura_max');
            set('custom_manequim_min','manequim_min'); set('custom_manequim_max','manequim_max');
            set('custom_calcado_min','calcado_min'); set('custom_calcado_max','calcado_max');
            set('custom_camiseta_min','camiseta_min'); set('custom_camiseta_max','camiseta_max');
            
            // Pega automáticos (que movemos)
            sb.querySelectorAll('select').forEach(s => { 
                if(!s.id.includes('custom_')) { 
                    if(s.value) np.set(s.name,s.value); else np.delete(s.name); 
                }
            });
            
            if(inp.value) np.set('q',inp.value);
            np.delete('p'); np.delete('e');
            window.location.search = np.toString();
        };

        // Popula valores ao carregar
        const pop = (id,k)=>{ if(p.get(k)) document.getElementById(id).value = p.get(k); };
        pop('custom_idade_min','idade_min'); pop('custom_idade_max','idade_max');
        pop('custom_altura_min','altura_min'); pop('custom_altura_max','altura_max');
        pop('custom_manequim_min','manequim_min'); pop('custom_manequim_max','manequim_max');
        pop('custom_calcado_min','calcado_min'); pop('custom_calcado_max','calcado_max');
        pop('custom_camiseta_min','camiseta_min'); pop('custom_camiseta_max','camiseta_max');

        // --- 3.6 RECONSTRÓI AÇÕES EM MASSA ---
        const actSel = document.querySelector('select[name="action"]');
        const actDiv = document.querySelector('.actions');
        if(actSel && actDiv && !document.querySelector('.custom-action-buttons')) {
            actSel.style.display='none'; 
            if(actDiv.querySelector('button')) actDiv.querySelector('button').style.display='none';
            
            const cnt = document.createElement('div'); 
            cnt.className = 'custom-action-buttons'; 
            cnt.innerHTML='<span>AÇÕES EM MASSA:</span>';
            
            Array.from(actSel.options).forEach(o => {
                if(!o.value) return;
                const b = document.createElement('button'); b.type='button'; b.className='action-btn-custom';
                const t = o.text.toLowerCase();
                
                if(t.includes('aprov')) { b.classList.add('btn-act-approve'); b.innerHTML='<i class="fas fa-check"></i> APROVAR'; }
                else if(t.includes('reprov')) { b.classList.add('btn-act-reject'); b.innerHTML='<i class="fas fa-times"></i> REPROVAR'; }
                else if(t.includes('excluir')) { b.classList.add('btn-act-delete'); b.innerHTML='<i class="fas fa-trash"></i> EXCLUIR'; }
                else { b.classList.add('btn-act-delete'); b.innerText=o.text; }
                
                b.onclick = () => { if(t.includes('excluir')&&!confirm('Confirmar?'))return; actSel.value=o.value; actDiv.closest('form').submit(); };
                cnt.appendChild(b);
            });
            actDiv.appendChild(cnt);
            
            const chk = () => { cnt.style.display = document.querySelectorAll('.action-select:checked').length>0?'flex':'none'; };
            document.body.addEventListener('change', (e) => { if(e.target.classList.contains('action-select')||e.target.id==='action-toggle') chk(); });
        }
    }

    // Inicializa
    setInterval(() => { attemptCount++; initListView(); initDetailView(); }, CHECK_INTERVAL);
})();