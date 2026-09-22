console.log("Sherlock iniciou!")
function BuscarDados(){
  
    return document.title;

}

chrome.runtime.onMessage.addListener((mensagem,sender, sendResponse)=>{

if(mensagem.action === "BuscarDados"){
    const titulo = BuscarDados();
    sendResponse({
        title : titulo
    });
}

});
