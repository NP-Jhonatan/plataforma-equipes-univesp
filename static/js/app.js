/* Equipes Univesp — scripts de interface.
 * 1. Barra de acessibilidade (tamanho da fonte e alto contraste), com preferência salva.
 * 2. Contador de caracteres acessível para campos com limite.
 * 3. Envio do interesse em participar pela API REST (fetch), sem recarregar a página.
 * Tudo funciona sem JavaScript também: os formulários continuam enviando normalmente.
 */
(function () {
  "use strict";

  function salvar(chave, valor) { try { localStorage.setItem(chave, valor); } catch (e) { /* ignorado */ } }

  function anunciar(texto, tipo) {
    var area = document.getElementById("avisos");
    if (!area) return;
    var div = document.createElement("div");
    div.className = "alert alert-" + (tipo || "success");
    div.setAttribute("role", tipo === "danger" ? "alert" : "status");
    div.textContent = texto;
    area.innerHTML = "";
    area.appendChild(div);
  }

  // ---------- 1. Acessibilidade ----------
  var raiz = document.documentElement;
  var btnContraste = document.getElementById("btn-contraste");
  if (btnContraste) {
    btnContraste.setAttribute("aria-pressed", raiz.classList.contains("alto-contraste"));
    btnContraste.addEventListener("click", function () {
      var ativo = raiz.classList.toggle("alto-contraste");
      btnContraste.setAttribute("aria-pressed", ativo);
      salvar("altoContraste", ativo ? "1" : "0");
    });
  }
  document.querySelectorAll("[data-fonte]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var passo = parseInt(btn.dataset.fonte, 10);
      var atual = parseInt(raiz.style.fontSize, 10) || 100;
      var novo = passo === 0 ? 100 : Math.min(150, Math.max(80, atual + passo));
      raiz.style.fontSize = novo + "%";
      salvar("tamanhoFonte", novo);
    });
  });

  // Leva o foco ao resumo de erros do formulário, quando existir.
  var resumo = document.getElementById("resumo-erros");
  if (resumo) resumo.focus();

  // ---------- 2. Contador de caracteres ----------
  document.querySelectorAll("[data-contador][maxlength]").forEach(function (campo) {
    var limite = parseInt(campo.getAttribute("maxlength"), 10);
    var contador = document.createElement("div");
    contador.className = "contador";
    contador.id = campo.id + "_contador";
    // Região separada para leitores de tela: anuncia só em marcos (evita falar a cada tecla).
    var aviso = document.createElement("div");
    aviso.className = "visually-hidden";
    aviso.setAttribute("aria-live", "polite");
    campo.insertAdjacentElement("afterend", aviso);
    campo.insertAdjacentElement("afterend", contador);
    var descritos = (campo.getAttribute("aria-describedby") || "").trim();
    campo.setAttribute("aria-describedby", (descritos + " " + contador.id).trim());

    var marcos = [50, 20, 10, 0];
    function atualizar() {
      var restante = limite - campo.value.length;
      contador.textContent = restante + " caracteres restantes";
      if (marcos.indexOf(restante) !== -1) aviso.textContent = restante + " caracteres restantes";
    }
    campo.addEventListener("input", atualizar);
    atualizar();
  });

  // ---------- 3. Interesse via API ----------
  var form = document.getElementById("form-interesse");
  if (form && window.fetch) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var botao = form.querySelector("button[type=submit]");
      var csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
      var mensagem = form.querySelector("[name=mensagem]");
      botao.disabled = true;
      botao.textContent = "Enviando…";

      fetch(form.dataset.api, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, "Accept": "application/json" },
        body: JSON.stringify({ mensagem: mensagem ? mensagem.value : "" })
      })
        .then(function (resp) { return resp.json().then(function (dados) { return { ok: resp.ok, dados: dados }; }); })
        .then(function (r) {
          if (!r.ok) throw new Error(r.dados.detail || "Não foi possível enviar seu interesse.");
          var bloco = document.createElement("div");
          bloco.innerHTML = '<p class="mb-0">Seu pedido: <span class="badge status-interesse-pendente">Aguardando resposta</span></p>';
          form.replaceWith(bloco);
          anunciar("Interesse enviado! O autor do projeto vai avaliar seu pedido.", "success");
        })
        .catch(function (erro) {
          botao.disabled = false;
          botao.textContent = "Tenho interesse em participar";
          anunciar(erro.message, "danger");
        });
    });
  }
})();
