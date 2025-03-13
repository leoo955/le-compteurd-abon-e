import discord
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import pickle
from google.auth.transport.requests import Request
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

def authenticate():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
            creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

youtube = authenticate()

def extract_channel_id(url_or_handle):
    if url_or_handle.startswith("https://www.youtube.com/channel/"):
        return url_or_handle.split("/")[-1]
    
    if url_or_handle.startswith("https://www.youtube.com/@") or url_or_handle.startswith("@"):
        handle = url_or_handle.split("@")[-1]
        request = youtube.search().list(part="snippet", type="channel", q=handle, maxResults=1)
        response = request.execute()
        if "items" in response and response["items"]:
            return response["items"][0]["id"]
    
    return url_or_handle

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

@bot.command()
async def follow(ctx, url_or_id: str):
    channel_id = extract_channel_id(url_or_id)
    info = get_channel_info(channel_id)

    if not info:
        await ctx.send("❌ Chaîne introuvable. Vérifie l'ID ou l'URL !")
        return

    embed = discord.Embed(title=info["name"], url=info["url"], color=0xFF0000)
    embed.set_thumbnail(url=info["profile_pic"])
    embed.set_footer(text=f"Nombre d'abonnés : {info['subscribers']} 🎥", icon_url="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg")

    await ctx.send(embed=embed)

bot.run(TOKEN)
