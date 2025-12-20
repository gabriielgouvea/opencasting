(function() {
    'use strict';

    // ============================================================
    // 0. CONFIGURAÇÕES GLOBAIS E DEPENDÊNCIAS
    // ============================================================
    const log = (msg) => console.log("%cOpenCasting CRM: " + msg, "color: #009688; font-weight: bold;");
    const CHECK_INTERVAL = 500;
    let searchDebounce = null;

    // Garante o carregamento do SweetAlert2 para os modais profissionais
    if (typeof Swal === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
        document.head.appendChild(script);
    }

    // ============================================================
    // 1. FUNÇÕES DE GESTÃO CRM (POP-UP E CÓPIA)
    // ============================================================

    // NOVO: Modal de Reprovação Inteligente (Suporta Individual e Massa)
    window.abrirModalReprovacao = function(id, event, isMassAction = false) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        Swal.fire({
            title: '<span style="color: #d33; font-weight: 800;">REPROVAR / AJUSTE</span>',
            html: `
                <div style="text-align: left; font-family: sans-serif;">
                    <label style="font-weight:bold; display:block; margin-bottom:5px; color: #444;">Motivo principal:</label>
                    <select id="swal-motivo" class="swal2-select" style="width:100%; margin-bottom:15px; font-size: 0.9rem; border-radius: 8px;">
                        <option value="fotos_ruins">Fotos fora do padrão (Escuras/Selfie/Espelho)</option>
                        <option value="dados_incompletos">Dados incompletos ou incorretos</option>
                        <option value="perfil">Perfil não compatível no momento</option>
                        <option value="outros">Outros (especificar abaixo)</option>
                    </select>
                    
                    <label style="font-weight:bold; display:block; margin-bottom:5px; color: #444;">Orientação para o Promotor (E-mail):</label>
                    <textarea id="swal-obs" class="swal2-textarea" style="width:100%; height:90px; margin:0; padding: 10px; font-size: 0.9rem; border-radius: 8px;" placeholder="Explique o que ele deve corrigir..."></textarea>
                    
                    <div style="margin-top:20px; padding:15px; background:#f4f6f7; border-radius:10px; border:1px solid #d5dbdb; display:flex; align-items:center;">
                        <input type="checkbox" id="swal-retry" style="width:25px; height:25px; cursor: pointer;" checked>
                        <label for="swal-retry" style="margin-left:12px; margin-bottom:0; cursor:pointer; font-size:0.85rem; color: #2c3e50; line-height: 1.2;">
                            <strong>PERMITIR TENTAR NOVAMENTE AGORA?</strong><br>
                            <small>Marcado: Ele pode editar agora (Ajuste).<br>Desmarcado: Bloqueio de 120 dias (Reprovado).</small>
                        </label>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'CONFIRMAR',
            cancelButtonText: 'CANCELAR',
            preConfirm: () => {
                return {
                    motivo: document.getElementById('swal-motivo').value,
                    obs: document.getElementById('swal-obs').value,
                    pode_tentar: document.getElementById('swal-retry').checked
                };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                const data = result.value;
                if (isMassAction) {
                    // Lógica para Ação em Massa: Injeta campos no form e envia
                    const form = document.getElementById('changelist-form');
                    const params = [['motivo_massa', data.motivo], ['obs_massa', data.obs], ['pode_tentar_massa', data.pode_tentar]];
                    params.forEach(([n, v]) => {
                        let inp = document.createElement('input'); inp.type='hidden'; inp.name=n; inp.value=v; form.appendChild(inp);
                    });
                    document.querySelector('select[name="action"]').value = 'reprovar_modelos_massa';
                    form.submit();
                } else {
                    // Lógica Individual: Redireciona via URL
                    const q = new URLSearchParams(data).toString();
                    window.location.href = `/admin/core/userprofile/${id}/reprovar/?${q}`;
                }
            }
        });
    };

    // NOVO: Função para copiar o link de avaliação rápida
    window.copiarLinkAvaliacao = function(uuid) {
        const link = window.location.origin + '/avaliar/' + uuid + '/';
        navigator.clipboard.writeText(link).then(() => {
            Swal.fire({ icon: 'success', title: 'Copiado!', text: 'Link pronto para o cliente.', timer: 2000, showConfirmButton: false });
        });
    };

    // Máscara de Altura
    function applyHeightMask(e) {
        let v = e.target.value.replace(/\D/g, "");
        if (v.length > 3) v = v.slice(0, 3);
        if (v.length >= 2) v = v.slice(0, 1) + "." + v.slice(1);
        e.target.value = v;
    }

    // ============================================================
    // 2. MODO DETALHE (SIDEBAR DE AÇÕES NO PERFIL)
    // ============================================================
    function initDetailView() {
        const row = document.querySelector('.submit-row');
        if (!row || document.querySelector('.sidebar-custom-actions')) return;

        const panel = document.querySelector('.field-painel_acoes .readonly');
        if (panel) {
            const sb = document.createElement('div');
            sb.className = 'sidebar-custom-actions';
            const tmp = document.createElement('div');
            tmp.innerHTML = panel.innerHTML;
            
            const bdg = tmp.querySelector('.status-badge');
            if(bdg) {
                bdg.className = bdg.className.replace('status-', 'sidebar-status-badge badge-');
                sb.appendChild(bdg);
            }

            tmp.querySelectorAll('a, button').forEach(b => {
                b.classList.remove('btn-action');
                b.classList.add('sidebar-btn');
                if(b.className.includes('approve')) b.classList.add('sb-approve');
                else if(b.className.includes('reject')) b.classList.add('sb-reject');
                else if(b.className.includes('whatsapp')) b.classList.add('sb-whatsapp');
                else if(b.className.includes('password')) b.classList.add('sb-password');
                else b.classList.add('sb-reconsider');
                sb.appendChild(b);
            });
            row.appendChild(sb);
        }
    }

    // ============================================================
    // 3. MODO LISTA (FILTROS LATERAIS E TOOLBAR)
    // ============================================================
    function initListView() {
        const lst = document.getElementById('changelist');
        if (!lst || document.getElementById('custom-filter-toolbar')) return;

        log("Construindo Interface CRM...");

        // --- 3.1 GAVETA LATERAL ---
        const sb = document.createElement('div');
        sb.id = 'custom-sidebar-filter';
        sb.innerHTML = `
            <div class="sidebar-header"><h3>FILTROS</h3><button id="btn-close-filter">&times;</button></div>
            <div id="sidebar-content">
                <div class="filter-group-box"><label>FAIXA ETÁRIA</label><div class="range-inputs"><input type="number" id="custom_idade_min" placeholder="De"><input type="number" id="custom_idade_max" placeholder="Até"></div></div>
                <div class="filter-group-box"><label>ALTURA</label><div class="range-inputs"><input type="text" id="custom_altura_min" placeholder="1.60"><input type="text" id="custom_altura_max" placeholder="1.80"></div></div>
                <hr><div id="original-filters-place"></div><button id="btn-realizar-busca">APLICAR</button>
            </div>`;
        document.body.appendChild(sb);
        sb.querySelector('#custom_altura_min').addEventListener('input', applyHeightMask);
        sb.querySelector('#custom_altura_max').addEventListener('input', applyHeightMask);
        const bd = document.createElement('div'); bd.id = 'filter-backdrop'; document.body.appendChild(bd);

        // --- 3.2 TOOLBAR ---
        const tb = document.createElement('div'); tb.id = 'custom-filter-toolbar';
        tb.innerHTML = `
            <div class="toolbar-search-container"><i class="fas fa-search search-icon"></i><input type="text" id="toolbar-search-input" placeholder="Buscar..."></div>
            <div class="toolbar-actions"><button id="btn-open-filter"><i class="fas fa-filter"></i> FILTROS</button></div>
        `;
        const frm = document.getElementById('changelist-form');
        if(frm) frm.parentNode.insertBefore(tb, frm);

        const toggle = (e) => { if(e)e.preventDefault(); sb.classList.toggle('active'); bd.style.display = sb.classList.contains('active')?'block':'none'; };
        document.getElementById('btn-open-filter').onclick = toggle;
        document.getElementById('btn-close-filter').onclick = toggle;
        bd.onclick = toggle;

        // --- 3.3 SELECT2 FIX (MOVER FILTROS) ---
        const tgt = document.getElementById('original-filters-place');
        document.querySelectorAll('select:not([name="action"]):not([id^="custom_"])').forEach(s => {
            if(!tgt.contains(s)) {
                const wrap = document.createElement('div'); wrap.className = 'filter-group-box';
                s.classList.remove('select2-hidden-accessible'); s.style.display = 'block'; s.style.width = '100%';
                const l = document.createElement('label'); l.innerText = s.name.toUpperCase();
                wrap.appendChild(l); wrap.appendChild(s); tgt.appendChild(wrap);
            }
        });

        // --- 3.4 RECONSTRÓI AÇÕES EM MASSA (Onde ocorre a mágica) ---
        const actSel = document.querySelector('select[name="action"]');
        const actDiv = document.querySelector('.actions');
        if(actSel && actDiv && !document.querySelector('.custom-action-buttons')) {
            actSel.style.display='none';
            const cnt = document.createElement('div'); cnt.className = 'custom-action-buttons'; 
            cnt.innerHTML='<span>AÇÕES EM MASSA:</span>';
            
            Array.from(actSel.options).forEach(o => {
                if(!o.value) return;
                const b = document.createElement('button'); b.type='button'; b.className='action-btn-custom';
                const t = o.text.toLowerCase();

                if(t.includes('aprov')) { b.innerHTML='<i class="fas fa-check"></i> APROVAR'; b.classList.add('btn-act-approve'); }
                else if(t.includes('reprov')) { b.innerHTML='<i class="fas fa-times"></i> REPROVAR'; b.classList.add('btn-act-reject'); }
                else if(t.includes('excluir')) { b.innerHTML='<i class="fas fa-trash"></i> EXCLUIR'; b.classList.add('btn-act-delete'); }
                else { b.innerText=o.text.toUpperCase(); }

                b.onclick = (e) => {
                    if(t.includes('reprov')) {
                        // INTERCEPTA PARA REPROVAR EM MASSA COM O POP-UP
                        window.abrirModalReprovacao(null, e, true);
                    } else {
                        if(t.includes('excluir') && !confirm('Confirmar exclusão?')) return;
                        actSel.value=o.value; actDiv.closest('form').submit();
                    }
                };
                cnt.appendChild(b);
            });
            actDiv.appendChild(cnt);
            const chk = () => { cnt.style.display = document.querySelectorAll('.action-select:checked').length>0?'flex':'none'; };
            document.body.addEventListener('change', (e) => { if(e.target.classList.contains('action-select')||e.target.id==='action-toggle') chk(); });
        }

        // Busca ao clicar Aplicar
        document.getElementById('btn-realizar-busca').onclick = () => {
            const np = new URLSearchParams(window.location.search);
            const set = (id,k)=>{ const e=document.getElementById(id); if(e&&e.value) np.set(k,e.value); else np.delete(k); };
            set('custom_idade_min','idade_min'); set('custom_idade_max','idade_max');
            set('custom_altura_min','altura_min'); set('custom_altura_max','altura_max');
            window.location.search = np.toString();
        };
    }

    setInterval(() => { initListView(); initDetailView(); }, CHECK_INTERVAL);

})();