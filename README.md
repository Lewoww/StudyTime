
---

# 📚 StudyTime

Um bot para **Discord** que transforma o estudo em uma experiência **coletiva e divertida**!
Com ele, você e seus amigos podem entrar juntos em call, registrar o tempo de estudo automaticamente e competir em um **ranking** para ver quem se dedica mais.

## 🚀 Funcionalidades

* ⏱️ Conta automaticamente o tempo de estudo de cada usuário quando entram/saiem da call.
* 🏆 Cria um **ranking** com os membros que mais estudaram.
* 📊 Comando `!points` para ver quanto tempo você acumulou.
* 🎯 Sistema de **Pomodoro** para organizar seus ciclos de estudo e descanso.
* 🔔 Notificações no chat quando alguém começa ou termina de estudar.

## 📷 Exemplo de uso

* Entre em um canal de voz e seu tempo começará a ser contabilizado.
* Ao sair, o bot enviará uma mensagem mostrando quanto tempo você estudou.
* Use `!points` para ver seu progresso pessoal.
* Use `!leaderboard` para ver o ranking dos 5 melhores estudantes.

## 🛠️ Como rodar localmente

### Pré-requisitos

* Python 3.9+
* Dependências listadas em `requirements.txt`
* Uma conta e aplicação registrada no [Discord Developer Portal](https://discord.com/developers/applications)

### Passo a passo

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu-usuario/studyrankbot.git
   cd studyrankbot
   ```
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto:

   ```
   DISCORD_TOKEN=seu_token_aqui
   ```
4. Rode o bot:

   ```bash
   python main.py
   ```

## 📦 Estrutura do projeto

```
studyrankbot/
│── main.py          # Código principal do bot
│── requirements.txt # Dependências do projeto
│── .env.example     # Exemplo das variáveis de ambiente
│── .gitignore       # Arquivos ignorados pelo git
│── README.md        # Documentação do projeto
```

## 🔒 Segurança

* **Nunca exponha seu token** diretamente no código.
* O arquivo `.env` deve ser protegido e está listado no `.gitignore`.

## 🤝 Contribuições

Contribuições são super bem-vindas!
Abra uma issue ou envie um pull request com melhorias, correções ou novas ideias.

## 📜 Licença

Este projeto está sob a licença MIT.

---# StudyTime
