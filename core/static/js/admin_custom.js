(function() {
    function initAdminCustom() {
        const actionContainer = document.querySelector('div.actions');
        const actionSelect = document.querySelector('select[name="action"]');
        const goButton = document.querySelector('button[name="index"]');
        const resultList = document.getElementById('result_list'); // A tabela de dados

        // Evita rodar se não tiver ações ou se já tiver rodado
        if (!actionContainer || !actionSelect || document.querySelector('.custom-action-buttons')) return;

        console.log("OpenCasting: Ativando botões inteligentes...");

        // 1. ESCONDER MENU ANTIGO
        actionSelect.style.cssText = 'display: none !important;';
        if (goButton) goButton.style.cssText = 'display: none !important;';
        const label = actionContainer.querySelector('label');
        if (label) label.style.cssText = 'display: none !important;';

        // 2. CRIAR OS NOVOS BOTÕES (INVISÍVEIS NO INÍCIO)
        const btnContainer = document.createElement('div');
        btnContainer.className = 'custom-action-buttons';
        btnContainer.style.display = 'none'; // <--- Começa escondido!
        btnContainer.style.gap = '10px';
        btnContainer.style.alignItems = 'center';
        btnContainer.style.marginTop = '10px';
        btnContainer.style.padding = '10px';
        btnContainer.style.backgroundColor = '#f8f9fa';
        btnContainer.style.border = '1px solid #ddd';
        btnContainer.style.borderRadius = '5px';

        // Ícone de "Ações"
        const infoIcon = document.createElement('span');
        infoIcon.innerHTML = '<i class="fas fa-bolt" style="color:#009688;"></i>';
        infoIcon.style.marginRight = '10px';
        btnContainer.appendChild(infoIcon);

        // Gera os botões baseados no select original
        Array.from(actionSelect.options).forEach(opt => {
            if (!opt.value) return;

            const text = opt.text.toLowerCase();
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-sm action-btn-custom';
            btn.style.marginRight = '5px';
            btn.style.fontWeight = 'bold';
            btn.style.borderRadius = '20px';
            btn.style.padding = '5px 15px';
            btn.style.border = 'none';
            btn.style.transition = '0.3s';
            
            // Guarda o tipo de ação no botão para usarmos na lógica depois
            if (text.includes('aprov')) btn.dataset.type = 'approve';
            else if (text.includes('reprov')) btn.dataset.type = 'reject';
            else if (text.includes('senha')) btn.dataset.type = 'password';
            else btn.dataset.type = 'other';

            // Estilização
            if (text.includes('aprov')) {
                btn.style.backgroundColor = '#28a745'; 
                btn.style.color = 'white';
                btn.innerHTML = '<i class="fas fa-check"></i> Aprovar';
            } else if (text.includes('reprov')) {
                btn.style.backgroundColor = '#dc3545';
                btn.style.color = 'white';
                btn.innerHTML = '<i class="fas fa-times"></i> Reprovar';
            } else if (text.includes('senha')) {
                btn.style.backgroundColor = '#ffc107';
                btn.style.color = '#333';
                btn.innerHTML = '<i class="fas fa-envelope"></i> Enviar Senha';
            } else if (text.includes('excluir')) {
                btn.style.backgroundColor = '#6c757d';
                btn.style.color = 'white';
                btn.innerHTML = '<i class="fas fa-trash"></i> Excluir';
            } else {
                btn.style.backgroundColor = '#17a2b8';
                btn.style.color = 'white';
                btn.innerHTML = opt.text;
            }

            // Clique do Botão
            btn.onclick = function() {
                if (this.disabled) return; // Segurança extra
                if (text.includes('excluir') && !confirm('Tem certeza absoluta?')) return;
                
                actionSelect.value = opt.value;
                if(goButton) goButton.click();
                else actionContainer.closest('form').submit();
            };

            btnContainer.appendChild(btn);
        });

        // Insere na tela
        actionContainer.appendChild(btnContainer);
        actionContainer.style.display = 'block';

        // ============================================================
        // 3. A LÓGICA INTELIGENTE (MONITORAR SELEÇÃO)
        // ============================================================
        function updateButtonState() {
            // Pega todos os checkboxes marcados
            const checkedBoxes = document.querySelectorAll('input.action-select:checked');
            
            // REGRA 1: Se ninguém selecionado, esconde tudo
            if (checkedBoxes.length === 0) {
                btnContainer.style.display = 'none';
                return;
            }
            
            // Se tem alguém, mostra a barra
            btnContainer.style.display = 'flex';

            // Variáveis de controle
            let temAprovado = false;
            let temReprovado = false;

            // Varre as linhas selecionadas para ver o status atual
            checkedBoxes.forEach(box => {
                const row = box.closest('tr');
                // Tenta achar a coluna de status (geralmente tem a classe field-status_visual)
                const statusCell = row.querySelector('.field-status_visual');
                
                if (statusCell) {
                    const statusText = statusCell.innerText.toLowerCase();
                    if (statusText.includes('aprovado')) temAprovado = true;
                    if (statusText.includes('reprovado')) temReprovado = true;
                }
            });

            // Pega os botões que criamos
            const btnApprove = btnContainer.querySelector('button[data-type="approve"]');
            const btnReject = btnContainer.querySelector('button[data-type="reject"]');

            // REGRA 2: Bloqueia "Aprovar" se já tiver alguém aprovado na seleção
            if (btnApprove) {
                if (temAprovado) {
                    btnApprove.disabled = true;
                    btnApprove.style.opacity = '0.3';
                    btnApprove.style.cursor = 'not-allowed';
                    btnApprove.title = "Já está aprovado";
                } else {
                    btnApprove.disabled = false;
                    btnApprove.style.opacity = '1';
                    btnApprove.style.cursor = 'pointer';
                    btnApprove.title = "";
                }
            }

            // REGRA 3: Bloqueia "Reprovar" se já tiver alguém reprovado
            if (btnReject) {
                if (temReprovado) {
                    btnReject.disabled = true;
                    btnReject.style.opacity = '0.3';
                    btnReject.style.cursor = 'not-allowed';
                    btnReject.title = "Já está reprovado";
                } else {
                    btnReject.disabled = false;
                    btnReject.style.opacity = '1';
                    btnReject.style.cursor = 'pointer';
                    btnReject.title = "";
                }
            }
        }

        // Adiciona "ouvidos" (listeners) nos checkboxes da tabela
        // 1. Checkbox individual
        const allCheckboxes = document.querySelectorAll('input.action-select');
        allCheckboxes.forEach(box => {
            box.addEventListener('change', updateButtonState);
        });

        // 2. Checkbox "Selecionar Todos" (cabeçalho)
        const selectAllToggle = document.getElementById('action-toggle');
        if (selectAllToggle) {
            selectAllToggle.addEventListener('click', function() {
                // Pequeno delay para dar tempo do Django marcar as caixas
                setTimeout(updateButtonState, 100);
            });
        }
    }

    // Tenta rodar ao carregar e insiste um pouco caso o Jazzmin demore
    window.addEventListener('load', initAdminCustom);
    setInterval(initAdminCustom, 1000); 
})();