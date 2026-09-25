# Estado do Projeto RASTRO

*Este arquivo deve ser atualizado pelo agente Antigravity no final de cada sprint para manter o contexto vivo caso a sessão caia ou o limite de tokens seja alcançado.*

- **Data da Última Atualização**: 2026-09-25
- **Sprint Atual/Concluída**: **Todas as Sprints da Fase 1 (0 a 10) concluídas com sucesso**.
- **Fase**: **MVP V1 Funcional**. O RASTRO v1 está finalizado, com integração ponta a ponta e motor determinístico real operando localmente no Windows.

## O Que Foi Entregue (MVP Completo)
1. **Frontend Completo e Integrado**: `frontend/index.html` consumindo a API verdadeira e demonstrando resultados (Score, Risco, Elementos lidos e Findings) dinamicamente com base em dados de varreduras reais.
2. **Backend API Robusto**: FastAPI (`backend/main.py`) servindo endpoints e páginas estáticas. Inclui configuração dedicada para subprocessos no Windows via `run_server.py`.
3. **SSRF Guard Integrado**: `backend/security.py` impede scans de IPs locais (127.0.0.1, 10.x, 192.168.x) e bloqueia domínios internos, provendo extrema segurança ao rodar.
4. **Scraping Real (Playwright)**: `backend/scraper.py` acessa URLs, bloqueia requisições a imagens/mídia pesada para otimizar velocidade, aplica timeout e previne navegação maliciosa.
5. **Motor Determinístico de Dark Patterns**: `backend/analyzer.py` possui 6 regras de negócio estruturadas (Urgência, Escassez, Confirmshaming, Ancoragem, Pré-seleção e Overlay).

## Instruções Atuais de Uso (Runbook)
Para rodar a versão final do MVP:
```powershell
.venv\Scripts\activate
python run_server.py
```
- Acesse `http://localhost:8000` para testar o painel visual e analisar URLs reais.
- Acesse `http://localhost:8000/docs` para visualizar a documentação oficial da API (Swagger UI).

## Próximos Passos (Backlog - Fases Futuras)
- **Integração de LLM (Fase 2)**: Utilizar modelos de IA (ex: OpenRouter) para encontrar padrões subjetivos e contextuais no texto da página, complementando o determinístico.
- **Banco de Dados & Relatórios**: Criar banco SQL/NoSQL para manter histórico de análises por data e permitir exportação de relatório.
- **Deploy em Nuvem**: Mover para um ambiente de produção (VPS Linux, Docker, orquestração).

## Restrições ou Problemas Conhecidos Atuais
- O código original legado da extensão Chrome (arquivos na raiz como manifest e popups) não tem mais serventia, o foco mudou 100% para a plataforma Web SaaS.
- A máquina Windows local exige a flag `loop="none"` e uso da `WindowsProactorEventLoopPolicy` para que a integração Uvicorn + Playwright funcione adequadamente, garantido pelo `run_server.py`.
