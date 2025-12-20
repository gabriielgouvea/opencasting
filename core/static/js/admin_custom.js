(function() {
    'use strict';

    /**
     * ============================================================
     * 0. CONFIGURAÇÕES, LOGS E DEPENDÊNCIAS
     * ============================================================
     */
    const log = (msg) => console.log("%cOpenCasting CRM: " + msg, "color: #009688; font-weight: bold;");
    const CHECK_INTERVAL = 500;

    log("Carregando inteligência de gestão...");

    // Garante que o SweetAlert2 esteja pronto para os popups profissionais
    if (typeof Swal === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
        document.head.appendChild(script);
    }

    /**
     * ============================================================
     * 1. CORREÇÃO DO BUG DO MOUSE (DROPDOWNS QUE SOMEM)
     * ============================================================
     * Esta lógica garante que ao passar o mouse nos botões de grupo (Ações),
     * o menu permaneça aberto através de um "timer de tolerância" (delay).
     */
    function fixDropdownHover() {
        document.querySelectorAll('.btn-group-custom').forEach(group => {
            const dropdown = group.querySelector('.dropdown-content');
            let timer;

            if (!dropdown) return;

            group.onmouseenter = () => {
                clearTimeout(timer);
                dropdown.style.display = 'block';
            };

            group.onmouseleave = () => {
                // Delay de 200ms para permitir que o mouse chegue ao menu
                timer = setTimeout(() => {
                    dropdown.style.display = 'none';
                }, 200);
            };

            dropdown.onmouseenter = () => clearTimeout(timer);
            dropdown.onmouseleave = () => {
                timer = setTimeout(() => {
                    dropdown.style.display = 'none';
                }, 200);
            };
        });
    }

    /**
     * ============================================================
     * 2. LÓGICA DE SELEÇÃO RÁPIDA (POPUP DE CÓPIA)
     * ============================================================
     */
    
    // Função para marcar ou desmarcar absolutamente tudo
    window.selecionarTudo = function(status) {
        document.querySelectorAll('.swal-copy-grid input[type="checkbox"]').forEach(c => {
            c.checked = status;
        });
    };

    // Função para selecionar apenas os campos fundamentais solicitados
    window.selecionarBasico = function() {
        // Primeiro limpamos tudo
        window.selecionarTudo(false);
        
        // Lista de IDs dos campos que compõem o kit básico
        const basico = [
            'cp-nome', 
            'cp-cpf', 
            'cp-nascimento', 
            'cp-camiseta', 
            'cp-manequim', 
            'cp-endereco'
        ];
        
        basico.forEach(id => {
            const el = document.getElementById(id);
            if(el) el.checked = true;
        });
    };

    /**
     * ============================================================
     * 3. GERADOR DE INTERFACE PARA CÓPIA (TODAS AS INFORMAÇÕES)
     * ============================================================
     * Esta função gera o grid de checkboxes com todos os dados do banco.
     */
    function gerarGradeDeSelecao(dados) {
        return `
            <div style="text-align: left; font-family: sans-serif;">
                <div style="margin-bottom: 20px; display: flex; gap: 10px; border-bottom: 2px solid #eee; padding-bottom: 15px;">
                    <button type="button" class="btn-swal-quick" style="background:#444; color:white; padding: 6px 12px; border-radius: 4px; border:none; font-weight:bold; font-size: 0.7rem; cursor:pointer;" onclick="selecionarTudo(true)">SELECIONAR TUDO</button>
                    <button type="button" class="btn-swal-quick" style="background:#eee; padding: 6px 12px; border-radius: 4px; border:none; font-weight:bold; font-size: 0.7rem; cursor:pointer;" onclick="selecionarTudo(false)">LIMPAR</button>
                    <button type="button" class="btn-swal-quick" style="background:#009688; color:white; padding: 6px 12px; border-radius: 4px; border:none; font-weight:bold; font-size: 0.7rem; cursor:pointer;" onclick="selecionarBasico()">INFO. BÁSICAS</button>
                </div>

                <div class="swal-copy-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-height: 400px; overflow-y: auto; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                    <div class="cp-item"><input type="checkbox" id="cp-nome" data-field="Nome" data-val="${dados.nome}" checked> <label for="cp-nome">Nome</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-idade" data-field="Idade" data-val="${dados.idade}" checked> <label for="cp-idade">Idade</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-nascimento" data-field="Nasc." data-val="${dados.nascimento}"> <label for="cp-nascimento">Nascimento</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-cpf" data-field="CPF" data-val="${dados.cpf}"> <label for="cp-cpf">CPF</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-rg" data-field="RG" data-val="${dados.rg}"> <label for="cp-rg">RG</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-nac" data-field="Nacionalidade" data-val="${dados.nacionalidade}"> <label for="cp-nac">Nacionalidade</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-gen" data-field="Gênero" data-val="${dados.genero}"> <label for="cp-gen">Gênero</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-etnia" data-field="Etnia" data-val="${dados.etnia}"> <label for="cp-etnia">Etnia</label></div>
                    
                    <div class="cp-item"><input type="checkbox" id="cp-zap" data-field="WhatsApp" data-val="${dados.whatsapp}"> <label for="cp-zap">WhatsApp</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-insta" data-field="Instagram" data-val="${dados.instagram}"> <label for="cp-insta">Instagram</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-email" data-field="E-mail" data-val="${dados.email}"> <label for="cp-email">E-mail</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-endereco" data-field="Endereço" data-val="${dados.endereco}"> <label for="cp-endereco">Endereço</label></div>
                    
                    <div class="cp-item"><input type="checkbox" id="cp-altura" data-field="Altura" data-val="${dados.altura}m"> <label for="cp-altura">Altura</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-peso" data-field="Peso" data-val="${dados.peso}kg"> <label for="cp-peso">Peso</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-manequim" data-field="Manequim" data-val="${dados.manequim}"> <label for="cp-manequim">Manequim</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-calcado" data-field="Calçado" data-val="${dados.calcado}"> <label for="cp-calcado">Calçado</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-camiseta" data-field="Camiseta" data-val="${dados.camiseta}"> <label for="cp-camiseta">Camiseta</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-olhos" data-field="Olhos" data-val="${dados.olhos}"> <label for="cp-olhos">Olhos</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-cabelo" data-field="Cabelo" data-val="${dados.cabelo}"> <label for="cp-cabelo">Cabelo</label></div>
                    
                    <div class="cp-item"><input type="checkbox" id="cp-experiencia" data-field="Experiência" data-val="${dados.experiencia}"> <label for="cp-experiencia">Experiência</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-disponibilidade" data-field="Disp." data-val="${dados.disponibilidade}"> <label for="cp-disponibilidade">Disp.</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-ingles" data-field="Inglês" data-val="${dados.ingles}"> <label for="cp-ingles">Inglês</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-espanhol" data-field="Espanhol" data-val="${dados.espanhol}"> <label for="cp-espanhol">Espanhol</label></div>
                    
                    <div class="cp-item"><input type="checkbox" id="cp-banco" data-field="Banco" data-val="${dados.banco}"> <label for="cp-banco">Banco</label></div>
                    <div class="cp-item"><input type="checkbox" id="cp-pix" data-field="Chave PIX" data-val="${dados.pix}"> <label for="cp-pix">Chave PIX</label></div>
                </div>
                <style>
                    .cp-item { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
                    .cp-item input { width: 18px; height: 18px; cursor: pointer; }
                    .cp-item label { font-size: 0.8rem; cursor: pointer; margin: 0; font-weight: 600; color: #555; }
                </style>
            </div>
        `;
    }

    /**
     * ============================================================
     * 4. AÇÃO: GERAR TEXTO PARA O WHATSAPP (SELETIVO)
     * ============================================================
     */
    window.copiarInformacoesPerfil = function(dados) {
        Swal.fire({
            title: 'O QUE DESEJA ENVIAR?',
            html: gerarGradeDeSelecao(dados),
            showCancelButton: true,
            confirmButtonText: 'GERAR TEXTO',
            confirmButtonColor: '#009688',
            cancelButtonText: 'CANCELAR',
            preConfirm: () => {
                let msg = "*APRESENTAÇÃO - OPENCASTING*\n\n";
                const checks = document.querySelectorAll('.swal-copy-grid input[type="checkbox"]:checked');
                
                if (checks.length === 0) {
                    Swal.showValidationMessage('Selecione pelo menos uma informação!');
                    return false;
                }

                checks.forEach(c => {
                    msg += `*${c.getAttribute('data-field')}:* ${c.getAttribute('data-val')}\n`;
                });
                return msg;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                navigator.clipboard.writeText(result.value).then(() => {
                    Swal.fire({ icon: 'success', title: 'Copiado!', text: 'Texto pronto para o WhatsApp.', timer: 1500, showConfirmButton: false });
                });
            }
        });
    };

    /**
     * ============================================================
     * 5. AÇÃO: CONFIGURAR E COPIAR LINK PÚBLICO (SELETIVO)
     * ============================================================
     */
    window.configurarLinkPublico = function(dados) {
        Swal.fire({
            title: 'O QUE O CLIENTE PODE VER?',
            html: gerarGradeDeSelecao(dados),
            showCancelButton: true,
            confirmButtonText: 'GERAR LINK',
            confirmButtonColor: '#34495e',
            cancelButtonText: 'CANCELAR',
            preConfirm: () => {
                const checks = document.querySelectorAll('.swal-copy-grid input[type="checkbox"]:checked');
                if (checks.length === 0) {
                    Swal.showValidationMessage('Selecione os campos visíveis!');
                    return false;
                }
                
                // Transforma IDs selecionados em lista para a URL
                const campos = Array.from(checks).map(c => c.id.replace('cp-', '')).join(',');
                return `${window.location.origin}/perfil/${dados.uuid}/?show=${campos}`;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                navigator.clipboard.writeText(result.value).then(() => {
                    Swal.fire({ icon: 'success', title: 'Link Gerado!', text: 'Link seletivo copiado.', timer: 1500, showConfirmButton: false });
                });
            }
        });
    };

    /**
     * ============================================================
     * 6. GESTÃO DE ACESSOS E SENHAS (BACKEND)
     * ============================================================
     */
    window.copiarLinkSenha = function(id) {
        fetch(`/admin/core/userprofile/${id}/gerar-link-senha/`)
            .then(response => response.json())
            .then(data => {
                if (data.link) {
                    navigator.clipboard.writeText(data.link).then(() => {
                        Swal.fire({ icon: 'success', title: 'Link Manual!', text: 'Link de recuperação copiado.', timer: 2000, showConfirmButton: false });
                    });
                }
            })
            .catch(err => log("Erro ao buscar link: " + err));
    };

    /**
     * ============================================================
     * 7. ANÁLISE E REPROVAÇÃO (MODAIS)
     * ============================================================
     */
    window.abrirModalReprovacao = function(id, event) {
        if (event) { event.preventDefault(); event.stopPropagation(); }
        Swal.fire({
            title: '<span style="color: #d33; font-weight: 800;">REPROVAR / AJUSTE</span>',
            html: `
                <div style="text-align: left; font-family: sans-serif;">
                    <label style="font-weight:bold; display:block; margin-bottom:5px;">Motivo principal:</label>
                    <select id="sw-motivo" class="swal2-select" style="width:100%; margin-bottom:15px; border-radius: 8px;">
                        <option value="fotos_ruins">Fotos fora do padrão</option>
                        <option value="dados_incompletos">Dados incorretos</option>
                        <option value="perfil">Perfil não compatível</option>
                        <option value="outros">Outros</option>
                    </select>
                    <label style="font-weight:bold; display:block; margin-bottom:5px;">Observação:</label>
                    <textarea id="sw-obs" class="swal2-textarea" style="width:100%; height:80px; border-radius: 8px;"></textarea>
                    <div style="margin-top:15px; display:flex; align-items:center;">
                        <input type="checkbox" id="sw-retry" style="width:20px; height:20px;" checked>
                        <label for="sw-retry" style="margin-left:10px; font-weight:bold;">Permitir tentar novamente?</label>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'CONFIRMAR',
            preConfirm: () => {
                return { 
                    motivo: document.getElementById('sw-motivo').value, 
                    obs: document.getElementById('sw-obs').value, 
                    pode_tentar: document.getElementById('sw-retry').checked 
                };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                const q = new URLSearchParams(result.value).toString();
                window.location.href = `/admin/core/userprofile/${id}/reprovar/?${q}`;
            }
        });
    };

    /**
     * ============================================================
     * 8. UTILITÁRIOS E LOOP DE CONTROLE
     * ============================================================
     */
    function applyHeightMask(e) {
        let v = e.target.value.replace(/\D/g, "");
        if (v.length > 3) v = v.slice(0, 3);
        if (v.length >= 2) v = v.slice(0, 1) + "." + v.slice(1);
        e.target.value = v;
    }

    // Inicialização Contínua para detecção de elementos dinâmicos
    setInterval(() => {
        fixDropdownHover();
        
        // Aplica máscara se o campo de altura aparecer (modo edição)
        const hInp = document.getElementById('id_altura');
        if (hInp && !hInp.dataset.masked) {
            hInp.oninput = applyHeightMask;
            hInp.dataset.masked = "true";
        }
    }, CHECK_INTERVAL);

})();