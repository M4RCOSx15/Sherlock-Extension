async function analisarPagina() {
  // Pega a aba ativa atual
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  // Executa uma função dentro do contexto da página web aberta
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: obterDadosDaPagina
  }, (resultados) => {
    if (resultados && resultados[0]) {
      const dados = resultados[0].result;
      document.getElementById('titulo').innerText = `Título: ${dados.titulo}`;
      document.getElementById('paragrafos').innerText = `Parágrafos: ${dados.qtdParagrafos}`;
    }
  });
}

// Esta função roda DENTRO da página web do usuário
function obterDadosDaPagina() {
  return {
    titulo: document.title,
    qtdParagrafos: document.querySelectorAll('p').length
  };
}

analisarPagina();
