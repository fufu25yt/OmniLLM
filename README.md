# 🤖 Multi-LLM Discord Chatbot

[🇫🇷 Français](#-français) · [🇬🇧 English](#-english)



\

> **A powerful, persistent and fully configurable Discord chatbot supporting multiple LLM providers.**

Connect **OpenAI, Google Gemini, Anthropic Claude, Mistral and Ollama** to a single Discord bot, assign different models to individual channels, manage API keys dynamically and configure response triggers directly from Discord.

---

## 🇫🇷 Français

### ✨ Fonctionnalités

* 🔑 **Gestion dynamique des API**
  Ajoutez ou gérez vos clés API directement depuis Discord avec `/api_add`, sans modifier votre fichier `.env`.

* 🦙 **Support Ollama**
  Connectez des instances Ollama locales ou distantes avec `/add_local_ollama`.

* 🧩 **Multi-salon & Multi-modèle**
  Attribuez un fournisseur et un modèle différent à chaque salon Discord avec `/set_channel`.

* 🔄 **Failover automatique**
  En cas de `429 Rate Limit`, le bot met automatiquement la clé concernée en cooldown et tente une autre clé ou un autre fournisseur disponible.

* 💾 **Configuration persistante**
  Les clés API, configurations des salons et paramètres du bot sont sauvegardés automatiquement dans `config.json`.

* 💬 **Formatage Discord optimisé**
  Les réponses sont configurées pour exploiter le Markdown Discord :

  * **Gras**
  * `Code inline`
  * Blocs de code
  * ||Spoilers||

* 🎯 **Déclencheurs flexibles**

  * Réponse automatique dans les salons configurés
  * Mentions `@Bot`
  * Réponses à des messages
  * Messages privés (DM)

### 🧠 Fournisseurs supportés

| Fournisseur                             | Support |
| --------------------------------------- | :-----: |
| OpenAI                                  |    ✅    |
| Google Gemini                           |    ✅    |
| Anthropic Claude                        |    ✅    |
| Mistral                                 |    ✅    |
| Ollama                                  |    ✅    |
| Autres fournisseurs compatibles LiteLLM |    ⚙️   |

---

## 🛠️ Installation

### 1. Prérequis

* Python **3.10 ou supérieur**
* Un bot Discord
* Les clés API des fournisseurs que vous souhaitez utiliser

Créez votre bot depuis le [Discord Developer Portal](https://discord.com/developers/applications).

### 2. Cloner le projet

```bash
git clone https://github.com/fufu25yt/OmniLLM.git
cd OmniLLM
```

### 3. Installer les dépendances

```bash
pip install discord.py litellm python-dotenv
```

### 4. Configurer l'environnement

Créez un fichier `.env` à la racine du projet :

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

> ⚠️ Ne partagez jamais votre token Discord ou vos clés API publiquement.

### 5. Lancer le bot

```bash
python main.py
```

---

## 🎮 Commandes Slash

| Commande            | Description                                        |
| ------------------- | -------------------------------------------------- |
| `/api_add`          | Ajouter une clé API pour un fournisseur            |
| `/add_local_ollama` | Ajouter une instance Ollama locale ou distante     |
| `/set_channel`      | Associer un salon à un fournisseur et un modèle    |
| `/list_channels`    | Afficher les salons et modèles configurés          |
| `/api_list`         | Afficher les clés enregistrées et leur statut      |
| `/api_clear`        | Supprimer les clés API et configurations de salons |
| `/set_mod_role`     | Définir le rôle autorisé à administrer le bot      |
| `/config_triggers`  | Configurer les déclencheurs de réponse             |

### 🔐 Gestion des clés API

Les clés peuvent être ajoutées directement depuis Discord :

```text
/api_add
```

Le bot peut gérer plusieurs clés et appliquer automatiquement un **cooldown** lorsqu'une clé atteint une limite de requêtes.

---

## 🦙 Ollama

Vous pouvez connecter une instance Ollama locale ou distante :

```text
/add_local_ollama
```

Exemple de configuration :

```text
Host: 192.168.1.100:11434
Model: llama3.1
```

Cela permet d'utiliser des modèles locaux sans dépendre exclusivement des fournisseurs cloud.

---

## 📁 Configuration

La configuration persistante est stockée dans :

```text
config.json
```

Elle peut contenir notamment :

* Les clés API enregistrées
* Les fournisseurs configurés
* Les modèles utilisés
* Les associations salons → modèles
* Les cooldowns
* Les paramètres des triggers
* Le rôle modérateur

> 🔒 Ajoutez `config.json` et `.env` à votre `.gitignore` si ces fichiers contiennent des secrets.

Exemple de `.gitignore` :

```gitignore
.env
config.json
__pycache__/
*.pyc
```

---

## 🏗️ Architecture

```text
Discord
   │
   ▼
discord.py
   │
   ▼
Bot / Command Handler
   │
   ├── API Manager
   │      ├── OpenAI
   │      ├── Gemini
   │      ├── Claude
   │      ├── Mistral
   │      └── Ollama
   │
   ├── Channel Manager
   │
   ├── Rate Limit / Cooldown Manager
   │
   └── Persistent Configuration
              │
              ▼
         config.json
```

---

## 🔄 Fonctionnement du failover

Lorsqu'un fournisseur ou une clé retourne une erreur de type `429` :

```text
Request
   │
   ▼
API Key #1
   │
   ├── ✅ Success → Response
   │
   └── ❌ 429
          │
          ▼
      Cooldown
          │
          ▼
      API Key #2
          │
          ├── ✅ Success → Response
          │
          └── ❌ Error
                 │
                 ▼
          Next available key
```

Cela permet d'améliorer la disponibilité du bot lorsque plusieurs clés ou fournisseurs sont configurés.

---

## ⚙️ Configuration des triggers

Les réponses peuvent être activées ou désactivées selon vos besoins :

```text
/config_triggers
```

Vous pouvez notamment contrôler :

* 💬 Réponse automatique
* 🏷️ Mentions du bot
* ↩️ Réponses à des messages
* ✉️ Messages privés

---

## 📌 Exemple d'utilisation

Vous pouvez par exemple configurer :

```text
#general
→ OpenAI / GPT-5

#coding
→ Anthropic / Claude

#local-ai
→ Ollama / llama3.1

#creative
→ Gemini
```

Chaque salon peut ainsi utiliser un modèle différent sans modifier le code du bot.

---

## 🚀 Roadmap

* [ ] Interface web d'administration
* [ ] Statistiques d'utilisation
* [ ] Gestion des coûts par fournisseur
* [ ] Historique des conversations
* [ ] Support de nouveaux fournisseurs LiteLLM
* [ ] Configuration avancée par serveur Discord
* [ ] Import/export de configuration
* [ ] Docker / Docker Compose

---

# 🇬🇧 English

## ✨ Features

* 🔑 **Dynamic API Management**
  Add and manage API keys directly from Discord using `/api_add`, without modifying `.env`.

* 🦙 **Ollama Support**
  Connect local or remote Ollama instances using `/add_local_ollama`.

* 🧩 **Multi-Channel & Multi-Model**
  Assign a different provider and model to each Discord channel with `/set_channel`.

* 🔄 **Automatic Failover**
  When a provider returns a `429 Rate Limit`, the affected key is automatically placed on cooldown and another available key or provider can be used.

* 💾 **Persistent Configuration**
  API keys, channel mappings and bot settings are automatically stored in `config.json`.

* 💬 **Discord-Optimized Formatting**
  Responses are configured to make use of Discord Markdown:

  * **Bold**
  * `Inline code`
  * Code blocks
  * ||Spoilers||

* 🎯 **Flexible Triggers**

  * Automatic responses in configured channels
  * `@Bot` mentions
  * Message replies
  * Direct Messages (DMs)

## 🧠 Supported Providers

| Provider                           | Support |
| ---------------------------------- | :-----: |
| OpenAI                             |    ✅    |
| Google Gemini                      |    ✅    |
| Anthropic Claude                   |    ✅    |
| Mistral                            |    ✅    |
| Ollama                             |    ✅    |
| Other LiteLLM-compatible providers |    ⚙️   |

---

## 🛠️ Installation

### 1. Prerequisites

* Python **3.10+**
* A Discord Bot
* API keys for the providers you want to use

Create your bot through the [Discord Developer Portal](https://discord.com/developers/applications).

### 2. Clone the repository

```bash
git clone https://github.com/fufu25yt/OmniLLM.git
cd OmniLLM
```

### 3. Install dependencies

```bash
pip install discord.py litellm python-dotenv
```

### 4. Environment setup

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token_here
```

> ⚠️ Never expose your Discord token or API keys publicly.

### 5. Run the bot

```bash
python main.py
```

---

## 🎮 Slash Commands

| Command             | Description                                  |
| ------------------- | -------------------------------------------- |
| `/api_add`          | Add an API key for a provider                |
| `/add_local_ollama` | Connect a local or remote Ollama instance    |
| `/set_channel`      | Bind a channel to a provider and model       |
| `/list_channels`    | Display configured channels and models       |
| `/api_list`         | Display registered API keys and their status |
| `/api_clear`        | Remove API keys and channel configurations   |
| `/set_mod_role`     | Set the role allowed to administer the bot   |
| `/config_triggers`  | Configure response triggers                  |

---

## 🦙 Ollama

Connect a local or remote Ollama instance using:

```text
/add_local_ollama
```

Example:

```text
Host: 192.168.1.100:11434
Model: llama3.1
```

This allows the bot to use local LLMs without relying exclusively on cloud providers.

---

## 📁 Configuration

Persistent configuration is stored in:

```text
config.json
```

It may contain:

* Registered API keys
* Configured providers
* Selected models
* Channel → model mappings
* Cooldown information
* Trigger settings
* Moderator role configuration

> 🔒 Add `.env` and `config.json` to `.gitignore` if they contain secrets.

Example:

```gitignore
.env
config.json
__pycache__/
*.pyc
```

---

## 🏗️ Architecture

```text
Discord
   │
   ▼
discord.py
   │
   ▼
Bot / Command Handler
   │
   ├── API Manager
   │      ├── OpenAI
   │      ├── Gemini
   │      ├── Claude
   │      ├── Mistral
   │      └── Ollama
   │
   ├── Channel Manager
   │
   ├── Rate Limit / Cooldown Manager
   │
   └── Persistent Configuration
              │
              ▼
         config.json
```

---

## 🔄 Automatic Failover

When a provider or API key returns a `429` error:

```text
Request
   │
   ▼
API Key #1
   │
   ├── ✅ Success → Response
   │
   └── ❌ 429
          │
          ▼
      Cooldown
          │
          ▼
      API Key #2
          │
          ├── ✅ Success → Response
          │
          └── ❌ Error
                 │
                 ▼
          Next available key
```

This improves availability when multiple API keys or providers are configured.

---

## ⚙️ Trigger Configuration

Configure the bot's response triggers with:

```text
/config_triggers
```

Available triggers may include:

* 💬 Automatic channel responses
* 🏷️ Bot mentions
* ↩️ Message replies
* ✉️ Direct Messages

---

## 📌 Example

You can configure different models for different channels:

```text
#general
→ OpenAI / GPT-5

#coding
→ Anthropic / Claude

#local-ai
→ Ollama / llama3.1

#creative
→ Gemini
```

Each channel can use its own model without changing the bot's source code.

---

## 🚀 Roadmap

* [ ] Web administration interface
* [ ] Usage statistics
* [ ] Provider cost tracking
* [ ] Conversation history
* [ ] Additional LiteLLM providers
* [ ] Per-server Discord configuration
* [ ] Configuration import/export
* [ ] Docker / Docker Compose

---

## 📄 License

This project is distributed under the **MIT License**.

See [`LICENSE`](LICENSE) for more information.
