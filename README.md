<<<<<<< HEAD
# Nome do Projeto (corrigir depois)

*(Recomendação: Adicione aqui uma ou duas frases que descrevem o objetivo principal do seu projeto. O que ele faz? Qual problema ele resolve?)*

-----

## 1\. Sobre o Projeto (corrigir depois)

*(Recomendação: Detalhe um pouco mais sobre o projeto. Fale sobre as principais funcionalidades, a quem se destina e as tecnologias utilizadas. Ex: "Este projeto é uma API RESTful para gerenciar X, Y e Z, construída com Python, FastAPI e conectada a um banco de dados PostgreSQL via Supabase.")*

-----

## 2\. Pré-requisitos

Antes de começar, garanta que você tenha os seguintes softwares instalados e configurados em sua máquina:

  - **Git:** Essencial para o controle de versão.
  - **Docker Desktop:** Para a criação e gerenciamento dos contêineres da aplicação.
  - **Windows Subsystem for Linux (WSL) 2:** **(Usuários Windows)** É um requisito para o Docker Desktop funcionar corretamente.
  - **Make:** Para simplificar a execução de comandos Docker e de pipeline.
      - **Windows:** A instalação pode ser feita via [Chocolatey](https://chocolatey.org/install).
      - **Linux/macOS:** Geralmente instalado via gerenciadores de pacotes como `apt` ou `brew`.

-----

## 3\. 🚀 Configuração do Ambiente de Desenvolvimento

Siga os passos abaixo para clonar e configurar o projeto em seu ambiente local.

### 3.1. Clone o Repositório

Navegue até o diretório onde deseja salvar o projeto e execute o comando abaixo. Substitua a URL pelo link do seu repositório.

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 3.2. Instalação das Ferramentas

Caso não tenha alguma das ferramentas listadas nos pré-requisitos, siga os guias abaixo:

\<details\>
\<summary\>\<strong\>Clique para ver as instruções de instalação\</strong\>\</summary\>

#### Git

1.  Acesse [git-scm.com/downloads](https://git-scm.com/downloads) e instale a versão para o seu sistema.
2.  **No Windows**, marque a opção para adicionar o Git ao `PATH` do sistema durante a instalação.
3.  Verifique a instalação:
    ```bash
    git --version
    ```

#### Docker Desktop

1.  Acesse [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) e instale a versão para o seu sistema.
2.  Reinicie o computador se for solicitado.

#### WSL 2 (Apenas Windows)

O Docker Desktop para Windows precisa do WSL 2 atualizado.

1.  Abra o **PowerShell** ou **Terminal** como **Administrador**.
2.  Execute o comando:
    ```bash
    wsl --update
    ```

#### Make

  - **No Windows (via Chocolatey)**:

    1.  Primeiro, instale o [Chocolatey](https://chocolatey.org/install).
    2.  Depois, em um terminal como **Administrador**, execute:
        ```powershell
        choco install make -y
        ```

  - **No Linux (Debian/Ubuntu)**:

    ```bash
    sudo apt update && sudo apt install build-essential -y
    ```

  - **No macOS (via Homebrew)**:

    ```bash
    brew install make
    ```

\</details\>

3.3. Ambiente Virtual (.venv)
Para isolar as dependências do projeto, utilize um ambiente virtual.

Crie e ative o ambiente:

# Crie o ambiente
 ```bash
    python -m venv .venv
```

# Ative no Windows (PowerShell)
 ```bash
.\.venv\Scripts\activate
```

# Ative no Linux/macOS
 ```bash
source .venv/bin/activate
Instale as dependências:
Com o ambiente ativo (você verá (.venv) no terminal), execute:
```

 ```bash
pip install -r requirements.txt
Para desativar o ambiente, use o comando deactivate.
```

-----

## 4\. Executando o Projeto com Docker

Com o Docker Desktop em execução, use os seguintes comandos `make` na raiz do projeto para gerenciar a aplicação.

  - **Construir (ou reconstruir) a imagem Docker:**
    *Este comando lê o `Dockerfile` e cria a imagem da sua aplicação.*

    ```bash
    make build
    ```

  - **Iniciar o container da aplicação:**
    *Este comando sobe o container em modo "detached" (-d), ou seja, rodando em segundo plano.*

    ```bash
    make run
    ```

    > Após a execução, a aplicação estará acessível em: **http://localhost:8000** (ou a porta que você configurou no `.env`).

  - **Parar o container:**

    ```bash
    make stop
    ```

  - **Visualizar os logs do container (útil para depuração):**

    ```bash
    make logs
    ```

  - **Acessar o terminal do container (para comandos de shell):**

    ```bash
    make shell
    ```

-----

## 5\. Fluxo de Trabalho com Git

Siga este fluxo para garantir que suas alterações sejam enviadas corretamente ao repositório.

### 5.1. Sincronizando seu Ambiente

Antes de começar a trabalhar, garanta que sua branch local esteja atualizada com a versão mais recente do repositório remoto.

1.  Verifique em qual branch você está:
    ```bash
    git branch
    ```
2.  Se não estiver na sua branch de desenvolvimento (ex: `gustavodev`), mude para ela:
    ```bash
    git checkout gustavodev
    ```
3.  Atualize sua branch com as alterações da `master` (ou `main`):
    ```bash
    git pull origin master
    ```

### 5.2. Enviando Suas Alterações

Após concluir uma tarefa, siga os passos abaixo para enviar seu código.

1.  Verifique os arquivos que você modificou:

    ```bash
    git status
    ```

2.  Adicione os arquivos desejados ao "stage":

    ```bash
    # Para adicionar todos os arquivos modificados
    git add .

    # Para adicionar um arquivo específico
    git add app/caminho/do/arquivo.py
    ```

3.  Faça o commit das suas alterações com uma mensagem descritiva:

    ```bash
    git commit -m "feat: Adiciona funcionalidade de login"
    ```

    > **Dica:** Use prefixos como `feat:`, `fix:`, `docs:`, `chore:` para organizar seus commits (Conventional Commits).

4.  Envie o commit para o repositório remoto na sua branch:

    ```bash
    git push origin gustavodev
    ```

> **Importante:** Para funcionalidades que precisam ser validadas, envie suas alterações tanto para a sua branch de desenvolvimento (`gustavodev`) quanto para a branch de homologação (`homolog`). A subida para a `master` ocorrerá ao final de cada sprint.

-----

## 6\. Pipeline de Homologação (CI/CD)

Para garantir a qualidade e a integração contínua, execute a pipeline de pré-commit antes de enviar suas alterações.

1.  **Instalar dependências (se necessário):**
    *Este comando deve ser executado para instalar as bibliotecas Python do projeto.*

    ```bash
    make install-dep
    ```

    > **Nota:** É uma boa prática criar um ambiente virtual (`python -m venv .venv` e `source .venv/bin/activate`) antes de instalar as dependências localmente.

2.  **Rodar a pipeline de verificação:**
    *Este comando executa testes, linters e outras verificações de qualidade de código.*

    ```bash
    make pr-pipeline
    ```

-----

## 7\. Arquitetura do Projeto

A estrutura do projeto foi organizada para promover separação de responsabilidades, segurança e manutenibilidade.

  - **Organização do Código:** Todo o código-fonte da aplicação está centralizado no diretório `app/`.
  - **Acesso ao Banco de Dados:** A lógica de conexão e as configurações do banco de dados foram isoladas no diretório `db/`.
  - **Segurança:** Chaves de API, tokens e senhas foram removidos do código e são gerenciados através de variáveis de ambiente em um arquivo `.env`.
  - **Modelos de Dados:** A representação das tabelas do banco de dados (modelos) está definida no diretório `models/`.
  - **Módulos Python:** Arquivos `__init__.py` foram adicionados aos diretórios para permitir que sejam tratados como pacotes, facilitando as importações relativas.
  - **Otimização:** Os arquivos `.dockerignore` e `.gitignore` foram configurados para evitar que arquivos desnecessários (como logs, caches e dependências locais) sejam copiados para a imagem Docker ou versionados no Git, resultando em uma imagem menor e um repositório mais limpo.
=======
## 1. Sobre o Projeto

## 2. Configuração do Ambiente de Desenvolvimento


Este guia irá ajudá-lo a configurar corretamente seu ambiente de desenvolvimento para executar o projeto localmente utilizando Docker.

---

### 2.1 Requisitos

Certifique-se de ter os seguintes softwares instalados:

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Windows Subsystem for Linux (WSL) **atualizado**
- [Chocolatey](https://chocolatey.org/install) (somente no Windows)
- **Make** (instalado via Chocolatey no Windows, ou via gerenciadores de pacotes no Linux/macOS)

---

### 2.2 Instalação do Git

1. Acesse o site: [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Baixe e instale o Git para o seu sistema operacional.
3. Durante a instalação no **Windows**, selecione a opção para **adicionar o Git ao PATH do sistema**.
4. Após a instalação, confirme que está tudo certo:
   ```bash
   git --version
   ```
   

### 2.3 Instalação do Docker Desktop

1. Acesse: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)  
2. Baixe e instale o Docker Desktop para o seu sistema.  
3. Reinicie o computador se for solicitado.  

### 2.4 Atualização do WSL (Windows Subsystem for Linux)

O Docker precisa que o WSL esteja atualizado.  

1. Abra o **PowerShell** como Administrador.  
2. Execute o comando:  

    ```bash
    wsl --update
    ```
    

### 2.5 Instalação do Chocolatey (Windows)

1. Abra o **PowerShell** como Administrador.  
2. Execute o comando abaixo para instalar o Chocolatey:  

    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; `
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```

### 2.6 Instalação do Make

#### 2.6.1 No Windows (via Chocolatey)

Após instalar o Chocolatey, execute no PowerShell como Administrador:  

    ```
    choco install make -y
    ```

Verifique:

    ```
    wsl --update
    ```

#### 2.6.2 Em sistemas Unix (Linux/macOS)

No Ubuntu/Debian:

    ```
    sudo apt update && sudo apt install build-essential -y
    ```

No macOS (usando Homebrew):

    ```
    brew install make
    ```

### 2.7 Clonando o Projeto

1. Acesse o repositório no GitHub.  
2. Clique no botão verde **"Code"** e copie o link HTTPS (ex: `https://github.com/seu-usuario/seu-repositorio.git`).  
3. No terminal, navegue até o diretório onde deseja clonar e execute:  

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
```

4. Acesse a pasta do projeto:

```bash
cd seu-repositorio
```

### 2.8 Executando o Projeto Localmente

1. Verificando a Branch Atual

```bash
git branch
```

Se não estiver na branch correta, mude com:

```bash
git checkout gustavodev
```

2. Atualizando a Branch

Atualize com as alterações do repositório remoto:

```bash
git pull origin master
```

O mesmo para uma segunda branch, chamada homolog (criar uma branch local chamada homolog e sincronizar com a origem):


```bash
git pull origin homolog
```

3. Comandos Docker via Make

Com o Docker Desktop rodando, utilize os comandos abaixo na raiz do projeto:

- Criar/Recriar a imagem:

```bash
make docker-build
```

- Rodar o container:

```bash
make docker-run
```

> A aplicação estará acessível em: http://localhost:8000

- Parar o container:

```bash
make docker-stop
```

### 2.9 Subindo Alterações para o Repositório

1. Verificar o status

```bash
Git status
```

2. Adicionar arquivos:

- Para adicionar tudo:

```bash
Git add .
```

- Para adicionar arquivos específicos:

```bash
git add caminho/do/arquivo
```

3. Verificar novamente o status:

```bash
git status
```

4. Fazer o commit:

```bash
git commit -m "Descreva aqui o que foi alterado"
```

5. Enviar para sua branch:

```bash
git push origin gustavodev
```

> Para alterações funcionais, realize o commit para a sua branch, bem como para a branch de homolog.

> As cargas de homolog subirão para a branch mastes ao final de cada sprint. 

> Pipeline para homologação
> 1: Instalar as dependenvias como o comando `install-dep` 
> 2: Rodar a pipeline via comando `make pr-pipeline`


### 3.0 Arquitetura do projeto
1. Organização do Código: O código da aplicação foi todo movido para dentro da pasta app/ para melhor organização.

2. Configuração do Banco de Dados: A lógica de conexão com o banco de dados foi centralizada na nova pasta db/.

3. Estrutura de Pacotes Python: Foram adicionados arquivos __init__.py em todas as pastas para melhorar os imports.

4. Otimização: Foram criados os arquivos .dockerignore e .gitignore para otimizar a imagem Docker e manter o repositório limpo.

5. Segurança: As senhas e tokens (como do Supabase) foram movidos para um arquivo .env para não ficarem expostos no código.

6. Arquitetura: Foi criada a pasta models/ para separar a representação das tabelas do banco de dados.

>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
