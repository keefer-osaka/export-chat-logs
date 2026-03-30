---
name: setup
description: "Configure Telegram Bot Token, chat ID, timezone, language, and output format for the export-chat-logs plugin."
allowed-tools:
  - Bash
  - Read
disable-model-invocation: true
---

# Configure Telegram

1. Run the following command to display the current configuration status and inform the user:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh"
```

2. Ask the first question and **wait for the user's response** before continuing:

   > Please enter your **Telegram Bot Token** (type `skip` to keep current value)
   >
   > **Create a new Bot:**
   > 1. Search for `@BotFather` in Telegram and open a chat
   > 2. Send `/newbot`
   > 3. Follow the prompts to enter the bot name and username (must end with `bot`, e.g. `MyExportBot`)
   > 4. Once created, BotFather will reply with a Token in the format: `123456789:AAF...`
   >
   > **Get the Token for an existing Bot:**
   > 1. Find `@BotFather` in Telegram, send `/mybots`
   > 2. Select your bot → **API Token**

3. After receiving the Token, ask the second question and **wait for the user's response** before continuing:

   > Please enter your **Telegram Chat ID** (type `skip` to keep current value)
   >
   > **Get your personal chat_id:**
   > 1. Search for `@userinfobot` in Telegram and open a chat
   > 2. Send any message (e.g. `/start`)
   > 3. The bot will reply with your `id`, which is your chat_id (a number, e.g. `123456789`)
   >
   > **Get a group chat_id:**
   > 1. Add your bot to the group and grant it admin permissions
   > 2. Send any message in the group
   > 3. Open a browser and go to `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   > 4. Find the `"chat":{"id":...}` field; the group id is negative (e.g. `-100123456789`)

4. After receiving the Chat ID, ask the third question and **wait for the user's response** before continuing:

   > Please enter your **timezone offset** (integer, e.g. `8` for UTC+8 Taiwan, `9` for UTC+9 Japan, `-5` for UTC-5 EST; type `skip` to keep current value)

5. After receiving the timezone, ask the fourth question and **wait for the user's response** before continuing:

   > Select your **language** / 選擇**語言**:
   > - `en` — English (default)
   > - `zh-TW` — 繁體中文
   >
   > (Type `skip` to keep current value)

6. After receiving the language, ask the fifth question and **wait for the user's response** before continuing:

   > Select your **output format** / 選擇**輸出格式**:
   > - `html` — HTML with syntax highlighting and interactive charts (default)
   > - `md` — Markdown (plain text)
   >
   > (Type `skip` to keep current value)

7. After receiving all five values, run — pass `"skip"` for any field the user skipped:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-token.sh" "<token or skip>" "<chat_id or skip>" "<timezone or skip>" "<lang or skip>" "<format or skip>"
```

Stop after configuration is complete — do not proceed with the export flow.
