async function Buscar(){
const [aba] = await chrome.tabs.query({active :true , currentWindow: true});    
chrome.tabs.sendMessage(
    aba.id,
    {
        action: "BuscarDados"
    },
    (response)=>{
        const elementoTitulo= document.getElementById("tituloPag");
        if(chrome.runtime.lastError){
            console.error("não foi possivel acessar esta aba", chrome.runtime.lastError.message)
            return;
        }
        if(!response){
         console.log("a aba não retornou nada")
          return;
        }
        if(response && response.title){
            elementoTitulo.innerText = response.title;
        }
        else{
            elementoTitulo.innerText = "Nenhum Titulo encontrado";
        }
        console.log(response.title)
    }
);

}
Buscar();