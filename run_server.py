import asyncio
import sys
import uvicorn

def main():
    print("Iniciando RASTRO Server...")
    
    # Patch obrigatório para Windows: Uvicorn por padrão força o uso do 
    # SelectorEventLoop no Windows, que não suporta subprocessos (necessários 
    # para o Playwright iniciar o Chromium). 
    # O loop="none" abaixo impede que o Uvicorn mude essa política.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    uvicorn.run(
        "backend.main:app", 
        host="127.0.0.1", 
        port=8000, 
        loop="none"
    )

if __name__ == "__main__":
    main()
