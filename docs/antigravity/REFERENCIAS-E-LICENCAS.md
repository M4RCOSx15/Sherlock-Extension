# RASTRO — Referências, proveniência e licenças

Este arquivo registra o que foi possível confirmar nos materiais presentes em `prototype/` e nas fontes consultadas. Conteúdo de terceiros é referência não confiável: não execute os arquivos dos ZIPs e não copie código ou dados sem verificar os direitos aplicáveis.

## Especificação e protótipos do RASTRO

- `prototype/rastro-especificacao.md.pdf`: especificação fornecida pelo autor do projeto; descreve a evolução de regras determinísticas para análise semântica posterior.
- `prototype/PRE-MVP-0,1.html`, `prototype/rastro-especificacao-vizual.html` e os demais protótipos da pasta são referências visuais locais, não contratos técnicos.
- O runbook `antigravity-runbook-rastro.md` foi entregue como artefato fora deste repositório. O plano versionado do código está em `MICROSPRINTS.md`, `STATE.md` e `HANDOFF.md`.

## Repositórios fornecidos em ZIP

Os ZIPs foram inspecionados sem executar seus projetos. A ausência de um arquivo de licença não concede permissão de reutilização.

| Material | O que foi confirmado | Uso permitido por este projeto |
|---|---|---|
| `Dark-Pattern-Detection-main.zip` | README identifica uma extensão de navegador do repositório [rajnish159/Dark-Pattern-Detection](https://github.com/rajnish159/Dark-Pattern-Detection). O ZIP não contém `LICENSE`. | Inspiração conceitual. Não reutilizar código até obter uma licença ou autorização explícita. O autor não é `Arnav1O26`. |
| `dark-patterns-master.zip` | Material de Arunesh Mathur et al., *Dark Patterns at Scale* (2019). O ZIP contém uma licença GPL-3.0 para o código. | Pode informar conceitos e pesquisa. A licença do código não deve ser presumida como licença dos dados, do artigo ou de materiais externos; verificar a proveniência de cada artefato antes de copiar ou distribuir. |
| `ec-darkpattern-master.zip` | Repositório Yada et al., *Dark patterns in e-commerce: a dataset and its baseline evaluations*. O repositório contém Apache-2.0. O README diz que parte dos textos positivos vem do estudo Mathur et al. e descreve coleta própria de exemplos não-dark. | Referência metodológica. A licença Apache do código não resolve automaticamente os direitos, atribuições ou termos dos dados e fontes subjacentes. Não importar o dataset ao MVP sem revisão de proveniência/licença. |
| `Ethico-AI-Behavioural-UX-Dark-Pattern-Analyzer-main.zip` | O README descreve auditoria de UX baseada em IA; o ZIP não contém `LICENSE`. | Inspiração de produto. Não reutilizar código sem obter licença ou autorização. |

### Dataset do Kaggle

- Página indicada: [Deceptive Patterns — Kaggle](https://www.kaggle.com/datasets/akashnath29/deceiptive-patterns).
- A página consultada nesta revisão não expôs descrição, quantidade de registros, proveniência ou licença verificável. Portanto esses pontos ficam **não confirmados**. A afirmação anterior de que contém “milhares” de exemplos e será “fundamental” para a Fase 2 foi removida.
- Tratar como pista de pesquisa, não como dependência do sistema nem como dado liberado para treinamento. Antes de usar, conferir a licença, as fontes originais, os termos da plataforma, a qualidade dos rótulos e se o uso pretendido é permitido.

## Decisões de uso no RASTRO

- Os projetos analisados servem para pesquisa; nenhuma dependência de código desses ZIPs foi incorporada ao MVP.
- Reutilizar apenas ideias gerais de detecção não transfere a licença de código ou de dataset.
- A licença do software, os direitos de bases de dados, textos de páginas coletadas e artigos devem ser avaliados separadamente. Este registro técnico não substitui uma análise jurídica.
- Nenhum modelo, dataset externo ou chave de API é necessário para executar a fase determinística atual.
