# MindDesk

## 1. Sobre o Projeto

### Sobre a MindDesk
A MindDesk é uma startup de tecnologia criada dentro da UniFecaf por um grupo de alunos de Análise e Desenvolvimento de Sistemas que compartilham uma visão comum: usar IA moderna, automação e agentes inteligentes para resolver problemas reais de eficiência nas empresas. Desde o início, o foco foi em um ponto crítico que atravessa organizações de todos os portes: o **RH está sobrecarregado** por processos manuais, informações dispersas e dependência constante de suporte humano. Nosso core é justamente atacar essa dor. Essencialmente, tratamos de transformar dúvidas corporativas em algo acessível, organizado e inteligente, elevando a produtividade de toda a organização.

### Nosso Time
<img width="1125" alt="Image" src="https://github.com/user-attachments/assets/c690ab0a-fdd0-4cd1-8004-208e50cfc696">

---

### 1.1 Visão do Produto

#### O Problema
Organizações de grande porte (como Vale, IBM e Banco do Brasil) compartilham um desafio recorrente: **processos de onboarding ineficientes**. Profissionais recém-admitidos enfrentam diversas dúvidas sobre tarefas iniciais, procedimentos, solicitação de acessos, documentos necessários e a quem contatar internamente para tirar essas dúvidas. Essa falta de clareza gera atrasos, dependência excessiva de funcionários mais experientes e uma sobrecarga significativa no time de Recursos Humanos, que passa a atuar como suporte operacional para dúvidas básicas e repetitivas.

#### Proposta de Valor
Desenvolvemos uma plataforma que centraliza todas as etapas e informações do onboarding, tornando o processo estruturado, acessível e guiado. O objetivo é proporcionar uma adaptação mais rápida e transparente, oferecendo autonomia inicial ao novo colaborador. A solução inclui funcionalidades como gerenciamento de PDFs (documentos internos) e consultas em linguagem natural por meio de um chat, permitindo que o colaborador encontre respostas rapidamente sem depender de outras áreas.

#### Produto Mínimo Viável (MVP)
Nosso MVP (Minimum Viable Product) é direcionado a empresas de pequeno e médio porte que possuem processos de onboarding estabelecidos, mas ainda dependem de interações humanas e de informações dispersas. A solução é totalmente escalável e modular, permitindo evoluir para um portal completo de suporte operacional não apenas para onboarding, mas para qualquer fluxo interno, política ou procedimento.

#### Métricas de Sucesso
Segundo uma pesquisa, somente 12% dos trabalhadores dizem que o onboarding da sua empresa realmente funciona bem, e cerca de um terço das organizações nem sequer possui um processo de onboarding estruturado (fonte: HR Chief).

> **Ociosidade e Produtividade:** Hoje, em um time de 40 pessoas com turnover considerado “saudável” (5% a 10% ao ano) e um onboarding que leva 3 meses, a empresa acumula o equivalente a **12 meses de ociosidade** — ou seja, paga por um funcionário inteiro que não está produzindo.

Com a implementação da nossa solução, buscamos atingir os seguintes objetivos:
* **Reduzir em pelo menos 50%** o tempo total do processo de onboarding, diminuindo retrabalhos, eliminando dúvidas recorrentes e acelerando o início da produtividade dos novos funcionários.
* **Reduzir em pelo menos 30%** o tempo perdido em ociosidade gerada por rotatividade, diminuindo significativamente o período necessário para treinar e integrar novos colaboradores.

---

## 2. Arquitetura e Tecnologias

### Arquitetura do Sistema
Optamos pelo padrão **MVC (Model–View–Controller)** devido à clara separação de responsabilidades entre backend e frontend, o que facilita adaptações futuras no frontend sem interferir na lógica interna. Essa separação também simplifica a manutenção e reduz o risco de regressões na aplicação.

* **Linguagem:** Python 3.9 (pelo amplo suporte a bibliotecas fundamentais).
* **Containerização:** Docker (garantindo portabilidade, independentemente do ambiente de execução e simplificando o deploy).
* **Segurança:** Variáveis de ambiente protegidas dentro do container.
* **Porta:** `8000`.

### 2.1 Back-end, Autenticação e Fluxo de Ingestão

#### Autenticação
O fluxo inicia com um mecanismo de login via **JWT (JSON Web Token)**, garantindo que apenas usuários autenticados possam interagir com a plataforma.
* **Novo Colaborador:** Acessa somente o chat de Consulta para dúvidas sobre o onboarding.
* **Gerente/Admin:** Além de consultar no chat, também acessa o fluxo de ingestão de documentos e arquivos sobre o onboarding.

#### Fluxo de Ingestão (Admin/Gerente)
O upload de documentos é estruturado nas seguintes etapas:
1.  **Upload de Documentos:** O administrador realiza o upload de documentos de onboarding (PDF, DOCX ou texto bruto), associando metadados (área, processo, prioridade).
2.  **Limpeza e Segmentação:** Os arquivos passam pelo serviço de pré-processamento, que realiza extração de texto, correção de encoding, remoção de ruído e chunking (particionamento textual).
3.  **Geração de Embeddings:** Para cada chunk, o embedding é gerado, os vetores são normalizados, e metadados são anexados.
4.  **Armazenamento e Indexação:** O sistema salva texto e metadados no banco e persiste os vetores na tabelada vetorial `pgvector`, atualizando índices de status para o texto salvo.

### 2.2 Pipeline de Qualidade Local
Embora não haja pipeline externa, implementamos processos locais rigorosos para manter o padrão do código:
1.  **Format:** Garante formatação consistente e padronizada.
2.  **Lint:** Aplica análise estática seguindo o padrão **PEP8**, identificando inconsistências e potenciais problemas.
3.  **Bandit:** Realiza análise de segurança do código para identificar vulnerabilidades óbvias.
4.  **Radon:** Verifica a **complexidade ciclomática** das funções, ajudando a manter uma arquitetura limpa e sustentável.

### 2.3 Front-end e UX
A interface da MindDesk foi projetada para ser simples, coerente e focada em produtividade. O fluxo visual foi concebido em **Figma**, com telas de acesso (cadastro, login, recuperação de senha) em alta fidelidade (**Hi-Fi**), utilizando tons escuros e elementos suaves para reduzir atrito e aumentar clareza.

**Módulos Principais:**
* **Painel do Gerente:** Após a autenticação, direciona para o painel com funções essenciais: upload de PDF (com Drag & Drop ou seleção manual), gerenciamento de funcionários, acesso ao chat e logout. Uma tabela lista todos os arquivos enviados.
* **Registro de Funcionários:** Formulário simples para adicionar novos colaboradores, seguido de uma tabela com lista de funcionários (ID, nome, e-mail, função e ações).
* **Chat de Consulta:** Ambiente de consulta principal com barra lateral de navegação e painel central minimalista.

---

## 3. Banco de Dados

Utilizamos o **Supabase**, que oferece um PostgreSQL gerenciado com suporte nativo à extensão `pgvector`, permitindo combinar um modelo relacional com capacidade de busca semântica.

O banco foi projetado para manter **integridade**, aplicando chaves primárias e estrangeiras, regras de validação via `CHECK` e campos obrigatórios definidos com `NOT NULL`. Na camada de performance, utilizamos **índices adequados** para cada tipo de operação, mantendo o armazenamento normalizado. Foram criadas duas tabelas principais (`pdf_vectors` e `pdf_uploads`) para o fluxo de busca vetorizada, e a tabela `users` para controle de acesso.

### Dicionário de Tabelas

<img width="733" height="521" alt="Image" src="https://github.com/user-attachments/assets/d2d67b5a-4013-40e3-a787-8bfab0703b4f" />

#### `pdf_vectors` (Busca Semântica)
Armazena os chunks dos documentos processados e seus embeddings.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | uuid | Identificador único de cada vetor gerado. |
| `pdf_id` | int8 | ID do PDF ao qual o chunk pertence (FK para `pdf_uploads`). |
| `chunk_text` | text | Trecho de texto extraído e limpo do documento. |
| `embedding` | vector | Vetor gerado pelo modelo de IA para busca semântica. |
| `chunk_index` | int4 | Posição sequencial do chunk no documento (ordem sequencial). |
| `embedding_model_used` | text | Nome/versão do modelo utilizado para gerar o embedding. |
| `created_at` | timestamptz | Momento em que o registro foi criado. |

#### `pdf_uploads` (Gestão de Arquivos)
Registro dos uploads realizados pelos administradores.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | uuid | Identificador interno do upload. |
| `user_id` | int8 | Usuário que enviou (FK). |
| `file_name` | text | Nome original do arquivo enviado. |
| `file_path` | text | Caminho onde o arquivo foi armazenado no sistema. |
| `uploaded_at` | timestamptz | Data e hora do upload. |
| `status` | text | Estado do arquivo (pendente, processado, erro, etc.). |

#### `users` (Controle de Acesso)

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | int8 | Identificador interno da aplicação. |
| `auth_user_id` | uuid | ID vinculado ao sistema nativo de autenticação do Supabase. |
| `name` | text | Nome do usuário. |
| `email` | text | E-mail utilizado para login e identificação. |
| `senha_hash` | text | Hash da senha (quando o login é gerenciado internamente). |
| `role` | text | Função do usuário (ex.: gerente, colaborador). |
| `ativo` | bool | Indica se o usuário está ativo ou desativado. |
| `created_at` | timestamptz | Momento de criação do registro no sistema. |

---

## 4. Inteligência Artificial e RAG

A camada de IA utiliza o padrão **RAG (Retrieval-Augmented Generation)**, atuando como núcleo da experiência do usuário. Adotamos o RAG para equilibrar desempenho, custo e confiabilidade.

* **Vantagem do RAG:** Em vez de enviar documentos completos para o LLM a cada pergunta, o RAG recupera apenas os trechos relevantes armazenados no banco vetorial, o que reduz custos de operação e acelera o tempo de resposta, baseando-se exclusivamente em conteúdos oficiais.

### Fluxo de Ingestão e Consulta (Resumo)
1.  **Texto e perguntas** $\to$ **vetores**.
2.  **Busca por similaridade**.
3.  **Recuperação de trechos** (do banco vetorial).
4.  **Resposta precisa** (gerada pelo LLM).

### Avaliação e Escolha de Tecnologias

#### Extração de Documentos (PDFs)
Avaliamos as principais bibliotecas (MuPDF, PyPDF2, PDFPlumber, PDFMiner e Unstructured) em critérios como velocidade, precisão e consistência.

<img width="816" height="521" alt="Image" src="https://github.com/user-attachments/assets/0b60859c-37fa-48f9-bd32-6c419f423e19" />

> Os testes mostraram que **MuPDF** foi a biblioteca com **melhor equilíbrio** entre precisão e desempenho, sendo adotada como a solução padrão. Outras, como PyPDF2, demonstraram comportamentos atípicos (diversidade lexical elevada ou junções incorretas de palavras).

Além disso, avaliamos os principais modelos de RAG moderados dentro da biblioteca transformer, com base em métricas de HIT e Precision. Sendo a **GTE-Small** a nossa escolha.

![Image](https://github.com/user-attachments/assets/0f7793d8-eedf-45f5-919c-b7879d7d58cf)


#### Modelos de Linguagem (LLMs)
Como gerador final de resposta, opitamos por utilizar o modelo de LLM GPT-4 Mini, devido ao seu custo-beneficio e acessibilidade.


![Image](https://github.com/user-attachments/assets/3888ac52-75bf-4902-b06d-7777f3a46173)
> **Performance:** A combinação entre busca vetorial e GPT-4 Mini atingiu aproximadamente **90% de acerto** nas respostas produzidas nas simulações.