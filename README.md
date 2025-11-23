# MindDesk

## 1. Sobre o Projeto

### Sobre a MindDesk
A MindDesk é uma startup de tecnologia criada dentro da UniFecaf por um grupo de alunos de Análise e Desenvolvimento de Sistemas que compartilham uma visão comum: usar IA moderna, automação e agentes inteligentes para resolver problemas reais de eficiência nas empresas.

Desde o início, o foco foi em um ponto crítico que atravessa organizações de todos os portes: o **RH está sobrecarregado** por processos manuais, informações dispersas e dependência constante de suporte humano. Nosso core é justamente atacar essa dor. Essencialmente, tratamos de transformar dúvidas corporativas em algo acessível, organizado e inteligente, elevando a produtividade de toda a organização.

### Nosso Time
<p align="center">
  <img src="./static/images/logo.png" alt="Nosso time de colaboradores" width="200">
</p>

---

### 1.1 Visão do Produto

#### O Problema
Organizações de grande porte (como Vale, IBM e Banco do Brasil) compartilham um desafio recorrente: **processos de onboarding ineficientes**. Profissionais recém-admitidos enfrentam diversas dúvidas sobre tarefas iniciais, procedimentos e documentos. Essa falta de clareza gera atrasos, dependência excessiva de funcionários experientes e sobrecarga no time de RH.

> **Dado de Mercado:** Segundo a *HR Chief*, apenas 12% dos trabalhadores dizem que o onboarding de suas empresas funciona bem. Em um time de 40 pessoas, um onboarding lento pode gerar o equivalente a 12 meses de ociosidade acumulada ao ano.

#### Proposta de Valor
Desenvolvemos uma plataforma que centraliza todas as etapas do onboarding, tornando o processo estruturado e guiado. A solução inclui:
* Gerenciamento de PDFs (documentos internos).
* Consultas em linguagem natural via Chat.
* Autonomia para o novo colaborador.

#### Produto Mínimo Viável (MVP)
Nosso MVP é direcionado a PMEs que possuem processos de onboarding estabelecidos, mas dependem de interações humanas. A solução é escalável e modular, podendo evoluir para um portal completo de suporte operacional.

#### Métricas de Sucesso
* **Redução de 50%** no tempo total do processo de onboarding.
* **Redução de 30%** no tempo perdido em ociosidade gerada por rotatividade.
* Aceleração do início da produtividade dos novos funcionários.

---

## 2. Arquitetura e Tecnologias

### Arquitetura do Sistema
Optamos pelo padrão **MVC (Model–View–Controller)** devido à clara separação de responsabilidades entre backend e frontend.
* **Linguagem:** Python 3.9.
* **Containerização:** Docker (garantindo portabilidade entre macOS, Windows e Linux).
* **Segurança:** Variáveis de ambiente protegidas dentro do container.
* **Porta:** `8000`.

#### Pipeline de Qualidade Local
Embora não haja pipeline externo, implementamos processos locais rigorosos:
1.  **Format:** Garante formatação consistente.
2.  **Lint:** Análise estática (PEP8).
3.  **Bandit:** Análise de segurança para identificar vulnerabilidades.
4.  **Radon:** Verificação de complexidade ciclomática das funções.

### Front-end e UX
A interface (concebida no Figma) foca em produtividade com identidade visual *Dark/Clean*.
* **Fluxo Colaborador:** Acesso rápido ao Chat de Consulta.
* **Fluxo Gerente:** Painel para upload de arquivos (Drag & Drop), gestão de funcionários e configurações.

---

## 3. Banco de Dados

Utilizamos o **Supabase (PostgreSQL)** gerenciado, com suporte nativo à extensão `pgvector` para combinar modelo relacional e busca semântica.

### Dicionário de Tabelas

#### `pdf_vectors` (Busca Semântica)
Armazena os chunks dos documentos processados e seus embeddings.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | uuid | Identificador único de cada vetor gerado. |
| `pdf_id` | int8 | ID do PDF (FK para `pdf_uploads`). |
| `chunk_text` | text | Trecho de texto extraído e limpo. |
| `embedding` | vector | Vetor gerado pelo modelo de IA. |
| `chunk_index` | int4 | Posição sequencial do chunk no documento. |
| `embedding_model_used` | text | Versão do modelo utilizado. |
| `created_at` | timestamptz | Data de criação. |

#### `pdf_uploads` (Gestão de Arquivos)
Registro dos uploads realizados pelos administradores.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | uuid | Identificador interno do upload. |
| `user_id` | int8 | Usuário que enviou (FK). |
| `file_name` | text | Nome original do arquivo. |
| `file_path` | text | Caminho de armazenamento. |
| `uploaded_at` | timestamptz | Data e hora do upload. |
| `status` | text | Estado (pendente, processado, erro). |

#### `users` (Controle de Acesso)

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | int8 | Identificador interno da aplicação. |
| `auth_user_id` | uuid | ID vinculado ao Auth do Supabase. |
| `name` | text | Nome do usuário. |
| `email` | text | E-mail de login. |
| `role` | text | Função (ex.: gerente, colaborador). |
| `ativo` | bool | Status do usuário. |

---

## 4. Inteligência Artificial e RAG

A camada de IA utiliza o padrão **RAG (Retrieval-Augmented Generation)**. O sistema não envia documentos inteiros para a IA a cada pergunta; ele recupera apenas os trechos relevantes do banco vetorial, reduzindo custos e alucinações.

### Fluxo de Ingestão e Consulta
1.  **Upload:** Admin envia PDF/DOCX.
2.  **Pré-processamento:** Uso da biblioteca **MuPDF** (escolhida por melhor performance em testes contra PyPDF2 e PDFMiner) para limpeza e extração.
3.  **Vetorização:** Texto segmentado em chunks e transformado em embeddings.
4.  **Busca:** A pergunta do usuário é vetorizada e comparada por similaridade no banco.
5.  **Geração:** O LLM (**GPT-4 Mini**) gera a resposta baseada apenas nos trechos recuperados.

> **Performance:** O motor de retorno vetorial combinado com GPT-4 Mini atingiu **~90% de acerto** nas respostas durante simulações.

---