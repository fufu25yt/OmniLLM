import os
import json
import asyncio
import time
import discord
from discord import app_commands
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"

# --- SYSTEM PROMPT (CHATBOT & DISCORD FORMATTING) ---
SYSTEM_PROMPT = """You are a friendly, helpful, and engaging chatbot on Discord.
Respond naturally to users.

Mandatory Discord formatting rules:
1. Use bold text to highlight important elements: **text**
2. Wrap code, commands, or technical values with code formatting: `code` (or ```language blocks for long code)
3. Use spoiler masks when content needs to be hidden: ||hidden text||
4. Keep responses concise and formatted properly for Discord."""

# --- DEFAULTS ---
DEFAULT_DATA = {
    "config": {
        "mod_role_id": int(os.getenv("MOD_ROLE_ID")) if os.getenv("MOD_ROLE_ID") and os.getenv("MOD_ROLE_ID").isdigit() else None,
        "allow_dm": os.getenv("ALLOW_DM", "False").lower() in ("true", "1", "yes"),
        "trigger_mention": True,
        "trigger_reply": True,
        "channels": {}  # Format: {"channel_id_str": {"provider": "ollama", "model": "llama3"}}
    },
    "api_pool": []
}

# --- PERSISTENCE FUNCTIONS (JSON) ---
def load_data():
    if not os.path.exists(CONFIG_FILE):
        save_data(DEFAULT_DATA["config"], DEFAULT_DATA["api_pool"])
        return DEFAULT_DATA["config"], DEFAULT_DATA["api_pool"]
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = data.get("config", DEFAULT_DATA["config"])
            if "channels" not in config:
                config["channels"] = {}
                
            api_pool = data.get("api_pool", [])
            for api in api_pool:
                api["cooldown_until"] = 0
                api["errors"] = 0
            return config, api_pool
    except Exception as e:
        print(f"⚠️ Error reading {CONFIG_FILE}: {e}. Loading defaults.")
        return DEFAULT_DATA["config"], DEFAULT_DATA["api_pool"]

def save_data(config, api_pool):
    clean_pool = []
    for api in api_pool:
        item = {
            "provider": api["provider"],
            "model": api["model"],
            "key": api.get("key", "")
        }
        if "api_base" in api:
            item["api_base"] = api["api_base"]
        clean_pool.append(item)
        
    data = {
        "config": config,
        "api_pool": clean_pool
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Load data at startup
CONFIG, API_POOL = load_data()

# --- DISCORD INITIALIZATION ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def is_authorized(interaction: discord.Interaction) -> bool:
    if interaction.guild and interaction.guild.owner_id == interaction.user.id:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    if CONFIG["mod_role_id"] and interaction.guild:
        role = interaction.guild.get_role(CONFIG["mod_role_id"])
        if role and role in interaction.user.roles:
            return True
    return False

# --- LLM ENGINE ---
async def get_llm_response(prompt: str, channel_id: int = None) -> str:
    if not API_POOL:
        return "❌ No API keys registered. Use `/api_add` or `/add_local_ollama`."

    now = time.time()
    ch_id_str = str(channel_id) if channel_id else None
    
    # Check if the channel has a specific model assigned
    target_api = None
    if ch_id_str and ch_id_str in CONFIG.get("channels", {}):
        ch_conf = CONFIG["channels"][ch_id_str]
        # Search for matching provider/model in the pool
        for api in API_POOL:
            if api["provider"] == ch_conf["provider"] and api["model"] == ch_conf["model"]:
                if api.get("cooldown_until", 0) <= now:
                    target_api = api
                    break

    # If no channel-specific rule or target API is on cooldown, use available pool
    candidates = [target_api] if target_api else [api for api in API_POOL if api.get("cooldown_until", 0) <= now]

    if not candidates or candidates[0] is None:
        return "⏳ API services configured for this channel are currently rate-limited. Please try again in a moment."

    for api in candidates:
        provider = api["provider"]
        model = api["model"]
        model_name = model if provider == "openai" else f"{provider}/{model}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        kwargs = {
            "model": model_name,
            "messages": messages
        }
        
        if api.get("key") and api["key"] != "none":
            kwargs["api_key"] = api["key"]
            
        if "api_base" in api:
            kwargs["api_base"] = api["api_base"]

        try:
            response = await asyncio.to_thread(completion, **kwargs)
            api["errors"] = 0
            return response.choices[0].message.content

        except Exception as e:
            err_str = str(e).lower()
            api["errors"] = api.get("errors", 0) + 1
            
            if "429" in err_str or "rate limit" in err_str or "quota" in err_str:
                api["cooldown_until"] = time.time() + 60
                print(f"[API] {provider}/{model} rate-limited. Cooling down for 60s.")
            else:
                print(f"[API Error] {provider}/{model}: {e}")
            continue

    return "❌ Failed to retrieve a response from the configured AI provider."

# --- SLASH COMMANDS ---

@tree.command(name="api_add", description="[Admin/Mod] Add a remote API key (OpenAI, Gemini, Claude...)")
@app_commands.choices(provider=[
    app_commands.Choice(name="OpenAI", value="openai"),
    app_commands.Choice(name="Google Gemini", value="gemini"),
    app_commands.Choice(name="Anthropic (Claude)", value="anthropic"),
    app_commands.Choice(name="Mistral AI", value="mistral"),
])
async def api_add(interaction: discord.Interaction, provider: app_commands.Choice[str], model: str, api_key: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    prov_val = provider.value.lower().strip()
    API_POOL.append({
        "provider": prov_val,
        "model": model.strip(),
        "key": api_key.strip(),
        "cooldown_until": 0,
        "errors": 0
    })
    
    save_data(CONFIG, API_POOL)
    await interaction.response.send_message(
        f"✅ API key registered! (`{prov_val}/{model}` - Total: `{len(API_POOL)}`)", 
        ephemeral=True
    )

@tree.command(name="add_local_ollama", description="[Admin/Mod] Add a local or remote Ollama instance")
async def add_local_ollama(interaction: discord.Interaction, ip_port: str, model: str):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    # Clean and format Ollama URL
    raw_ip = ip_port.strip().rstrip("/")
    if not raw_ip.startswith("http://") and not raw_ip.startswith("https://"):
        api_base = f"http://{raw_ip}"
    else:
        api_base = raw_ip

    API_POOL.append({
        "provider": "ollama",
        "model": model.strip(),
        "key": "none",
        "api_base": api_base,
        "cooldown_until": 0,
        "errors": 0
    })

    save_data(CONFIG, API_POOL)
    await interaction.response.send_message(
        f"🦙 Ollama registered! Model: `{model}` at `{api_base}`",
        ephemeral=True
    )

@tree.command(name="set_channel", description="[Admin/Mod] Bind a Discord channel to a specific provider/model")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel, provider: str = None, model: str = None):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    ch_id_str = str(channel.id)

    if not provider or not model:
        # Remove channel-specific rule
        if ch_id_str in CONFIG["channels"]:
            del CONFIG["channels"][ch_id_str]
            save_data(CONFIG, API_POOL)
            await interaction.response.send_message(f"📌 Channel {channel.mention} reset (will use fallback pool).", ephemeral=True)
        else:
            await interaction.response.send_message(f"📌 Channel {channel.mention} had no specific configuration.", ephemeral=True)
        return

    # Save channel-to-model mapping
    CONFIG["channels"][ch_id_str] = {
        "provider": provider.lower().strip(),
        "model": model.strip()
    }
    save_data(CONFIG, API_POOL)

    await interaction.response.send_message(
        f"📌 Channel {channel.mention} is now configured to use `{provider.lower()}/{model}`.",
        ephemeral=True
    )

@tree.command(name="list_channels", description="[Admin/Mod] List channels and their assigned AI models")
async def list_channels(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    channels_config = CONFIG.get("channels", {})
    if not channels_config:
        await interaction.response.send_message("No channel-specific configurations found.", ephemeral=True)
        return

    msg = "**Channel Configurations:**\n"
    for ch_id, data in channels_config.items():
        msg += f"- <#{ch_id}> ➡️ `{data['provider']}/{data['model']}`\n"

    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="api_list", description="[Admin/Mod] List registered API instances")
async def api_list(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    if not API_POOL:
        await interaction.response.send_message("No API keys or instances registered.", ephemeral=True)
        return

    msg = "**Registered API Pool:**\n"
    now = time.time()
    for idx, api in enumerate(API_POOL):
        status = "🟢 Active" if api.get("cooldown_until", 0) <= now else f"🔴 Cooling down ({int(api['cooldown_until'] - now)}s)"
        base_info = f" ({api['api_base']})" if "api_base" in api else ""
        msg += f"`{idx + 1}.` **{api['provider']}/{api['model']}**{base_info} - {status}\n"

    await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="api_clear", description="[Admin/Mod] Clear all API keys and channel settings")
async def api_clear(interaction: discord.Interaction):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    API_POOL.clear()
    CONFIG["channels"].clear()
    save_data(CONFIG, API_POOL)
    await interaction.response.send_message("🗑️ All API keys and channel bindings have been cleared.", ephemeral=True)

@tree.command(name="set_mod_role", description="[Admin/Owner] Set the moderator role for bot configuration")
async def set_mod_role(interaction: discord.Interaction, role: discord.Role = None):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    CONFIG["mod_role_id"] = role.id if role else None
    save_data(CONFIG, API_POOL)
    role_name = role.mention if role else "None"
    await interaction.response.send_message(f"⚙️ Moderator role set to: {role_name}", ephemeral=True)

@tree.command(name="config_triggers", description="[Admin/Mod] Configure bot interaction triggers")
async def config_triggers(interaction: discord.Interaction, mention: bool = None, reply: bool = None, allow_dm: bool = None):
    if not is_authorized(interaction):
        await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
        return

    if mention is not None: CONFIG["trigger_mention"] = mention
    if reply is not None: CONFIG["trigger_reply"] = reply
    if allow_dm is not None: CONFIG["allow_dm"] = allow_dm

    save_data(CONFIG, API_POOL)
    msg = (
        f"**Trigger Configuration Saved:**\n"
        f"- Mention (@Bot): `{'Yes' if CONFIG['trigger_mention'] else 'No'}`\n"
        f"- Reply: `{'Yes' if CONFIG['trigger_reply'] else 'No'}`\n"
        f"- Direct Messages (DM): `{'Yes' if CONFIG['allow_dm'] else 'No'}`"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# --- DISCORD EVENTS ---

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot logged in as {client.user}")
    print(f"📁 Configuration loaded ({len(API_POOL)} API keys, {len(CONFIG.get('channels', {}))} channels bound)")

@client.event
async def on_message(message):
    if message.author == client.user or message.content.startswith("/"):
        return

    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_dm:
        if not CONFIG["allow_dm"]:
            return
        should_respond = True
        prompt = message.content
    else:
        should_respond = False
        prompt = ""
        ch_id_str = str(message.channel.id)

        # If channel has specific AI assignment, respond directly
        if ch_id_str in CONFIG.get("channels", {}):
            should_respond = True
            prompt = message.content

        elif CONFIG["trigger_mention"] and client.user.mentioned in message.mentions:
            should_respond = True
            prompt = message.content.replace(f"<@{client.user.id}>", "").replace(f"<@!{client.user.id}>", "").strip()

        elif CONFIG["trigger_reply"] and message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                if ref_msg.author == client.user:
                    should_respond = True
                    prompt = message.content
            except discord.NotFound:
                pass

    if should_respond and prompt:
        async with message.channel.typing():
            reply = await get_llm_response(prompt, channel_id=None if is_dm else message.channel.id)
            
            if len(reply) > 2000:
                for chunk in [reply[i:i+1900] for i in range(0, len(reply), 1900)]:
                    await message.reply(chunk) if not is_dm else await message.channel.send(chunk)
            else:
                await message.reply(reply) if not is_dm else await message.channel.send(reply)

if __name__ == '__main__':
    token = os.getenv("DISCORD_TOKEN")
    if token:
        client.run(token)
    else:
        print("Error: DISCORD_TOKEN is missing in the .env file.")