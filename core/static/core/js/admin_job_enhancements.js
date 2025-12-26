(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function normalizeCep(value) {
    return String(value || "").replace(/\D+/g, "").slice(0, 8);
  }

  async function fillAddressFromCep() {
    const cepInput = qs("#id_cep");
    if (!cepInput) return;

    const cep = normalizeCep(cepInput.value);
    if (cep.length !== 8) return;

    try {
      const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const data = await resp.json();
      if (!data || data.erro) return;

      const endereco = qs("#id_endereco");
      const bairro = qs("#id_bairro");
      const cidade = qs("#id_cidade");
      const estado = qs("#id_estado");

      if (endereco && !endereco.value) endereco.value = data.logradouro || "";
      if (bairro && !bairro.value) bairro.value = data.bairro || "";
      if (cidade && !cidade.value) cidade.value = data.localidade || "";
      if (estado && !estado.value) estado.value = data.uf || "";
    } catch (e) {
      // best-effort
    }
  }

  function formatTimeDigits(value) {
    const digits = String(value || "").replace(/\D+/g, "");
    if (digits.length === 4) {
      return `${digits.slice(0, 2)}:${digits.slice(2, 4)}`;
    }
    if (digits.length === 3) {
      return `0${digits.slice(0, 1)}:${digits.slice(1, 3)}`;
    }
    return value;
  }

  function initTimeMask() {
    function handle(el) {
      const v = el.value;
      const next = formatTimeDigits(v);
      if (next !== v) el.value = next;
    }

    const selector = "input[id$='hora_inicio'], input[id$='hora_fim'], input[name$='hora_inicio'], input[name$='hora_fim']";
    qsa(selector).forEach((el) => {
      if (el.dataset.ocTimeMaskInit === "1") return;
      el.dataset.ocTimeMaskInit = "1";
      el.addEventListener("blur", () => handle(el));
      el.addEventListener("change", () => handle(el));
    });

    // Quando adicionar novas linhas no inline
    document.body.addEventListener("click", (e) => {
      const t = e.target;
      if (t && (t.classList.contains("add-row") || t.closest(".add-row"))) {
        setTimeout(() => initTimeMask(), 50);
      }
    });
  }

  function initOutrosToggle() {
    const outrosInput = qs("#id_tipo_servico_outros");
    if (!outrosInput) return;

    const checkbox = qs("#id_tipo_servico input[value='outros']");

    function setVisible(visible) {
      const row = outrosInput.closest(".form-row") || outrosInput.closest(".form-group") || outrosInput.parentElement;
      if (!row) return;
      row.style.display = visible ? "" : "none";
      if (!visible) outrosInput.value = "";
    }

    function sync() {
      setVisible(Boolean(checkbox && checkbox.checked));
    }

    if (checkbox) checkbox.addEventListener("change", sync);
    sync();
  }

  document.addEventListener("DOMContentLoaded", function () {
    // CEP -> endereço
    const cepInput = qs("#id_cep");
    if (cepInput) {
      cepInput.addEventListener("blur", fillAddressFromCep);
      cepInput.addEventListener("change", fillAddressFromCep);
    }

    initTimeMask();
    initOutrosToggle();
  });
})();
