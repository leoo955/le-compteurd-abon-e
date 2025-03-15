import discord
import os
import googleapiclient.discovery
from discord.ext import commands
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialiser les intents Discord
intents = discord.Intents.default()
intents.message_content = True  # Permission pour lire les messages
bot = commands.Bot(command_prefix="/", intents=intents)

# Authentification YouTube avec API Key
def authenticate():
    return googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

youtube = authenticate()

# Fonction pour extraire l'ID d'une chaîne YouTube depuis une URL ou un @handle
def extract_channel_id(url_or_handle):
    if url_or_handle.startswith("https://www.youtube.com/channel/"):
        return url_or_handle.split("/")[-1]

    if url_or_handle.startswith("https://www.youtube.com/@") or url_or_handle.startswith("@"):
        handle = url_or_handle.split("@")[-1]
        request = youtube.channels().list(part="id", forHandle=handle)
        response = request.execute()
        if "items" in response and response["items"]:
            return response["items"][0]["id"]

    return url_or_handle  # Si c'est déjà un ID, on le renvoie

# Fonction pour récupérer les infos de la chaîne
def get_channel_info(channel_id):
    request = youtube.channels().list(part="snippet,statistics", id=channel_id)
    response = request.execute()

    if "items" not in response or not response["items"]:
        return None

    data = response["items"][0]
    return {
        "name": data["snippet"]["title"],
        "profile_pic": data["snippet"]["thumbnails"]["high"]["url"],
        "subscribers": data["statistics"]["subscriberCount"],
        "url": f"https://www.youtube.com/channel/{channel_id}"
    }

# Commande pour suivre une chaîne et afficher les abonnés
@bot.command()
async def follow(ctx, url_or_id: str):
    channel_id = extract_channel_id(url_or_id)
    info = get_channel_info(channel_id)

    if not info:
        await ctx.send("❌ Chaîne introuvable. Vérifie l'ID ou l'URL !")
        return

    embed = discord.Embed(title=info["name"], url=info["url"], color=0xFF0000)
    embed.set_thumbnail(url=info["profile_pic"])
    embed.set_footer(text=f"Nombre d'abonnés : {info['subscribers']} 🎥", 
                     icon_url="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg")

    await ctx.send(embed=embed)

# Commande de test pour voir si le bot fonctionne
@bot.command()
async def test(ctx):
    await ctx.send("✅ Le bot est bien en ligne et fonctionne !")

# Event pour afficher un message quand le bot est prêt
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

# Lancer le bot
bot.run(DISCORD_TOKEN)
