# Sistema de Estacionamento

Aplicativo desenvolvido em Python com Kivy/KivyMD para gerenciamento e visualização de estacionamentos.

O projeto está sendo dividido entre a equipe: a parte de layout/interface será desenvolvida por outros integrantes, enquanto a integração do ESP32 com o aplicativo será feita separadamente.

## Sobre o programa

Atualmente, o aplicativo permite:

- acessar a tela principal;
- adicionar um estacionamento por meio de um PIN;
- validar se o PIN possui 4 dígitos;
- verificar se o PIN existe nos dados cadastrados;
- impedir que o mesmo estacionamento seja adicionado mais de uma vez;
- exibir os estacionamentos conectados;
- mostrar a quantidade de vagas ocupadas e o total de vagas;
- navegar entre a tela principal e a tela de inserção do PIN.

No momento, os estacionamentos e as vagas são simulados diretamente no código. Essa estrutura será substituída posteriormente pela integração com o ESP32.

## Tecnologias utilizadas

- Python
- Kivy
- KivyMD
- ESP32 — integração futura

## Estrutura do projeto

```text
.
├── main.py
├── Interface.kv
└── README.md
```

### `main.py`

Contém a lógica principal do aplicativo, incluindo:

- validação do PIN;
- armazenamento temporário dos estacionamentos;
- atualização da lista de estacionamentos;
- navegação entre telas;
- controle dos dados exibidos.

### `Interface.kv`

Contém a interface visual atual do aplicativo.

O layout definitivo será desenvolvido pela equipe responsável pela interface.

## Como executar

### 1. Instale o Python

É necessário ter o Python instalado no computador.

Para verificar:

```bash
python --version
```

Em alguns sistemas, o comando pode ser:

```bash
python3 --version
```

### 2. Instale as dependências

No terminal, execute:

```bash
pip install kivy kivymd
```

Caso o comando `pip` não funcione:

```bash
python -m pip install kivy kivymd
```

### 3. Mantenha os arquivos na mesma pasta

O `main.py` e o `Interface.kv` devem permanecer no mesmo diretório:

```text
projeto/
├── main.py
└── Interface.kv
```

### 4. Execute o aplicativo

Abra o terminal na pasta do projeto e execute:

```bash
python main.py
```

Ou, dependendo da configuração do sistema:

```bash
python3 main.py
```

## Funcionamento atual

O aplicativo inicia na tela principal.

Ao clicar no botão `+`, o usuário é direcionado para a tela de conexão de estacionamento.

Nessa tela, deve ser digitado um PIN de 4 dígitos.

Para testes, existem atualmente estes estacionamentos cadastrados:

```text
1234 -> Shopping Polo -> 32 vagas
5678 -> Shopping 2    -> 50 vagas
9012 -> Shopping 3    -> 20 vagas
```

Quando um PIN válido é informado, o estacionamento é adicionado à tela principal.

Cada estacionamento possui atualmente os seguintes dados:

```text
PIN
Nome
Vagas ocupadas
Vagas totais
```

A quantidade de vagas ocupadas começa em `0`, pois esse valor ainda será recebido do ESP32.

## Divisão do projeto

### Layout

A parte visual e o desenvolvimento do layout definitivo ficarão sob responsabilidade da equipe responsável pela interface.

Isso inclui alterações como:

- aparência das telas;
- cores;
- posicionamento dos componentes;
- estilo dos botões;
- tela de detalhes;
- melhorias visuais e de experiência do usuário.

### Integração com ESP32

A integração do ESP32 com o aplicativo será responsável por substituir os dados simulados por dados reais do estacionamento.

O objetivo é permitir que o aplicativo receba informações como:

```text
Quantidade de vagas ocupadas
Quantidade de vagas livres
Estado das vagas
Dados do estacionamento
```

## Próximas etapas

O desenvolvimento pode seguir esta ordem:

### Etapa 1 — Estrutura atual do aplicativo

- [x] Criar a tela principal.
- [x] Criar a tela para inserir o PIN.
- [x] Validar PIN de 4 dígitos.
- [x] Cadastrar estacionamentos de teste.
- [x] Exibir os estacionamentos conectados.
- [x] Exibir vagas ocupadas e vagas totais.
- [x] Impedir estacionamentos duplicados.

### Etapa 2 — Layout

- [ ] Finalizar o layout do aplicativo.
- [ ] Criar a tela de detalhes do estacionamento.
- [ ] Definir a exibição individual das vagas.
- [ ] Adicionar mensagens visuais de erro e confirmação.
- [ ] Ajustar a interface para diferentes tamanhos de tela.

Responsável: equipe de layout.

### Etapa 3 — ESP32

- [ ] Definir como o ESP32 enviará os dados.
- [ ] Definir o formato dos dados enviados.
- [ ] Fazer o ESP32 identificar o estado das vagas.
- [ ] Enviar os dados do ESP32 para o aplicativo.
- [ ] Receber os dados no Python.
- [ ] Atualizar `vagas_ocupadas` com dados reais.
- [ ] Atualizar a interface automaticamente quando os dados mudarem.

Responsável: integração ESP32.

### Etapa 4 — Substituir os dados de teste

Atualmente, o aplicativo usa dados fixos no `BANCO_DE_DADOS_TESTE`.

Depois da integração, será necessário substituir essa simulação por dados reais provenientes do ESP32, de uma API ou de um banco de dados, conforme a arquitetura definida pelo grupo.

- [ ] Remover ou desativar o banco de dados de teste.
- [ ] Buscar os dados reais do estacionamento.
- [ ] Associar cada estacionamento ao seu PIN.
- [ ] Carregar o total de vagas.
- [ ] Carregar a quantidade de vagas ocupadas.

### Etapa 5 — Atualização em tempo real

- [ ] Atualizar automaticamente os valores das vagas.
- [ ] Refletir mudanças do ESP32 sem reiniciar o aplicativo.
- [ ] Tratar perda de conexão.
- [ ] Tratar dados inválidos ou incompletos.

### Etapa 6 — Testes finais

- [ ] Testar PIN válido.
- [ ] Testar PIN inválido.
- [ ] Testar PIN inexistente.
- [ ] Testar estacionamento duplicado.
- [ ] Testar comunicação com o ESP32.
- [ ] Testar atualização das vagas.
- [ ] Testar perda e retorno da conexão.
- [ ] Testar o aplicativo em diferentes dispositivos.

## Atualização deste README

Conforme cada etapa for concluída, basta alterar:

```text
- [ ] Etapa pendente
```

para:

```text
- [x] Etapa concluída
```

Assim, o próprio README pode ser usado para acompanhar o andamento do projeto.
