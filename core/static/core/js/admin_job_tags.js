(function () {
  function uniqueTags(tags) {
    const out = [];
    const seen = new Set();
    for (const t of tags) {
      const v = (t || "").trim();
      if (!v) continue;
      const key = v.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(v);
    }
    return out;
  }

  function splitValue(value) {
    return uniqueTags(String(value || "")
      .split(/[,;|\n\r]+/g)
      .map((s) => s.trim())
      .filter(Boolean));
  }

  function joinValue(tags) {
    return uniqueTags(tags).join(", ");
  }

  function initTagInput(input) {
    if (input.dataset.tagInputInit === "1") return;
    input.dataset.tagInputInit = "1";

    const suggestionsRaw = input.getAttribute("data-suggestions") || "";
    const suggestions = suggestionsRaw
      .split("|")
      .map((s) => s.trim())
      .filter(Boolean);

    const wrapper = document.createElement("div");
    wrapper.className = "oc-tags";

    const chips = document.createElement("div");
    chips.className = "oc-tags__chips";

    const help = document.createElement("div");
    help.className = "oc-tags__help";
    help.textContent = "Enter adiciona • Backspace remove último";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(chips);
    wrapper.appendChild(input);
    wrapper.appendChild(help);

    // datalist com sugestões
    if (suggestions.length) {
      const dl = document.createElement("datalist");
      const dlId = `oc-tags-${Math.random().toString(16).slice(2)}`;
      dl.id = dlId;
      for (const s of suggestions) {
        const opt = document.createElement("option");
        opt.value = s;
        dl.appendChild(opt);
      }
      input.setAttribute("list", dlId);
      wrapper.appendChild(dl);
    }

    function render() {
      chips.innerHTML = "";
      const tags = splitValue(input.value);
      for (const t of tags) {
        const chip = document.createElement("span");
        chip.className = "oc-tags__chip";
        chip.textContent = t;

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "oc-tags__remove";
        btn.setAttribute("aria-label", `Remover ${t}`);
        btn.textContent = "×";
        btn.addEventListener("click", () => {
          const next = splitValue(input.value).filter((x) => x.toLowerCase() !== t.toLowerCase());
          input.value = joinValue(next);
          render();
        });

        chip.appendChild(btn);
        chips.appendChild(chip);
      }
    }

    function addTag(raw) {
      const value = (raw || "").trim();
      if (!value) return;
      const current = splitValue(input.value);
      current.push(value);
      input.value = joinValue(current);
      render();
    }

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addTag(input.value);
        // mantém só os tags (limpa qualquer digitação parcial duplicada)
        input.value = joinValue(splitValue(input.value));
        render();
        input.focus();
        return;
      }

      if (e.key === ",") {
        e.preventDefault();
        addTag(input.value);
        input.value = joinValue(splitValue(input.value));
        render();
        input.focus();
        return;
      }

      if (e.key === "Backspace" && !input.value.trim()) {
        const current = splitValue(input.value);
        if (current.length) {
          current.pop();
          input.value = joinValue(current);
          render();
          e.preventDefault();
        }
      }
    });

    input.addEventListener("blur", () => {
      input.value = joinValue(splitValue(input.value));
      render();
    });

    render();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[data-tag-input="1"]').forEach(initTagInput);
  });
})();
