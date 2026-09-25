# RASTRO - Referências e Materiais Analisados

Este documento compila os achados dos arquivos de referência fornecidos no diretório `prototype/` e outros locais, servindo de base de pesquisa para o projeto. Eles são dados de referência e **não ditam** a execução atual do agente, que deve ser guiada pelas Sprints.

## 1. Documentos de Especificação
- **`rastro-especificacao.md.pdf`**
  - **Uso:** A base primária de escopo do MVP. Ele divide o MVP em regras determinísticas rápidas (Fase 1: regex/CSS para urgência e escassez) e análise de linguagem emocional com IA (Fase 2). O foco está em performance, com o Playwright no backend extraindo apenas elementos relevantes e não dependendo de orquestração complexa.
- **`antigravity-runbook-rastro.md`**
  - **Uso:** Manual de execução e regras de conduta para o agente Antigravity, detalhando as microsprints e enfatizando as aprovações humanas.

## 2. Protótipos Visuais (Diretório `prototype/`)
- Existem múltiplos arquivos soltos e designs preliminares (como `Prototipo_v1`, `rastro-especificacao-vizual`, `PRE-MVP-0,1`). A Sprint 2 do MVP deve analisar essas pastas HTML/CSS estáticas para padronizar e adotar a estética final que o usuário aprovar (dark/terminal UI).

## 3. Repositórios e Projetos Analisados (Arquivos ZIP)
Esses arquivos não devem ser executados, mas seus repositórios no GitHub (ou arquivos de código dentro dos zips) fornecem abordagens interessantes:

- **`Arnav1O26/dark-pattern-detector` (`Dark-Pattern-Detection-main.zip`)**
  - **Uso Potencial:** Inspiração para a arquitetura backend (Python) combinando scraper e modelos clássicos (como TF-IDF ou regex). Usa interface em Streamlit/Plotly, o que não será seguido no RASTRO (já temos nosso frontend definido), mas a organização do scraper Python é útil de avaliar.
- **`ec-darkpattern-master.zip` e `dark-patterns-master.zip`**
  - **Uso Potencial:** Prováveis bancos de regras ou heurísticas de identificação em comércio eletrônico que podem ser usados para inspirar as regras de Regex/CSS (Fase 1).
- **`Ethico-AI-Behavioural-UX-Dark-Pattern-Analyzer-main.zip`**
  - **Uso Potencial:** Projeto avançado focado em auditoria ética. Pode inspirar o design do contrato de resposta da API sobre como classificar a "Força da Evidência" que é um requisito da Sprint 5.

## 4. Dataset (Kaggle)
- **`deceiptive-patterns`** (akashnath29 no Kaggle)
  - **Resumo:** Conjunto de dados contendo milhares de textos e trechos que são padrões enganosos.
  - **Uso no MVP:** Será fundamental na **Fase 2**, quando integrarmos o LLM e precisarmos construir o prompt do sistema (System Prompt) instruindo a IA sobre exemplos clássicos (few-shot prompting) para detecção de manipulação textual, misdirection e confirmshaming.

## Recomendações Baseadas em Pesquisa Recente (Setembro de 2026)
- **Scraping**: `Playwright` para Python continua sendo a ferramenta mais resiliente para lidar com sites modernos e Single Page Applications, dado seu isolamento robusto de contextos (útil contra vazamento de sessões).
- **LLM/VPS**: Os modelos pequenos da Google e Alibaba (Gemini Flash e Qwen-2.5) têm custo acessível e contexto longo, permitindo boa extração se o DOM for devidamente purgado (sem tags `<script>` e `<style>`) antes de passar pro LLM, diminuindo o uso de tokens consideravelmente. A OCI (Oracle Cloud Infrastructure) fornece a melhor VPS Always Free no formato ARM (Ampere A1), mas será preciso atentar à compatibilidade das imagens Docker do Playwright com a arquitetura ARM64 ao construir a imagem.
- **Contexto do Antigravity**: Confirmamos que na IDE pode não haver um hook perfeitamente automático e transparente do limite de tokens de janela sem intervenção; portanto, a limitação defensiva (atualização frequente de HANDOFF/STATE a cada sprint ou quando perto de estourar a memória de contexto visível) é a abordagem mais honesta e resiliente.
