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

*** Refatoração e Melhorias de Arquitetura
* Principais Mudanças Implementadas
Organização do Código: O código da aplicação foi todo movido para dentro da pasta app/ para melhor organização.

Configuração do Banco de Dados: A lógica de conexão com o banco de dados foi centralizada na nova pasta db/.

Estrutura de Pacotes Python: Foram adicionados arquivos __init__.py em todas as pastas para melhorar os imports.

Otimização: Foram criados os arquivos .dockerignore e .gitignore para otimizar a imagem Docker e manter o repositório limpo.

Segurança: As senhas e tokens (como do Supabase) foram movidos para um arquivo .env para não ficarem expostos no código.

Arquitetura: Foi criada a pasta models/ para separar a representação das tabelas do banco de dados.

