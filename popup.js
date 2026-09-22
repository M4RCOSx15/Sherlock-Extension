async function Buscar(){
const [aba] = await chrome.tabs.query({active :true , currentWindow: true});    
chrome.tabs.sendMessage(
    aba.id,
    {
        action: "BuscarDados"
    },
    (response)=>{
        console.log(response.title)
    }
);

}
Buscar();