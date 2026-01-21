import requests
from pathlib import Path
from PIL import Image
import io

# Caminho absoluto para o seu projeto no Windows
OUTPUT_DIR = Path(r"D:\projects\VaultKeeper\app\ui\icons\service_icons")

# Cria as pastas necessárias se não existirem
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SITES = {
    "google": "google.com",
    "github": "github.com",
    "gitlab": "gitlab.com",
    "bitbucket": "bitbucket.org",
    "stackoverflow": "stackoverflow.com",
    "microsoft": "microsoft.com",
    "apple": "apple.com",
    "openai": "openai.com",
    "anthropic": "anthropic.com",
    "docker": "docker.com",
    "aws": "aws.amazon.com",
    "vercel": "vercel.com",
    "netlify": "netlify.com",
    "cloudflare": "cloudflare.com",
    "heroku": "heroku.com",
    "digitalocean": "digitalocean.com",
    "firebase": "firebase.google.com",
    "supabase": "supabase.com",
    "postman": "postman.com",
    "python": "python.org",
    "discord": "discord.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "twitter.com",
    "x": "x.com",
    "linkedin": "linkedin.com",
    "reddit": "reddit.com",
    "whatsapp": "whatsapp.com",
    "telegram": "telegram.org",
    "slack": "slack.com",
    "twitch": "twitch.tv",
    "tiktok": "tiktok.com",
    "pinterest": "pinterest.com",
    "tumblr": "tumblr.com",
    "mastodon": "joinmastodon.org",
    "netflix": "netflix.com",
    "spotify": "spotify.com",
    "youtube": "youtube.com",
    "disneyplus": "disneyplus.com",
    "hbomax": "hbomax.com",
    "primevideo": "primevideo.com",
    "apple-tv": "tv.apple.com",
    "steam": "store.steampowered.com",
    "epicgames": "epicgames.com",
    "roblox": "roblox.com",
    "crunchyroll": "crunchyroll.com",
    "nintendo": "nintendo.com",
    "playstation": "playstation.com",
    "xbox": "xbox.com",
    "notion": "notion.so",
    "dropbox": "dropbox.com",
    "trello": "trello.com",
    "figma": "figma.com",
    "canva": "canva.com",
    "adobe": "adobe.com",
    "zoom": "zoom.us",
    "atlassian": "atlassian.com",
    "evernote": "evernote.com",
    "monday": "monday.com",
    "asana": "asana.com",
    "miro": "miro.com",
    "linear": "linear.app",
    "amazon": "amazon.com.br",
    "ebay": "ebay.com",
    "aliexpress": "aliexpress.com",
    "mercadolivre": "mercadolivre.com.br",
    "shopee": "shopee.com.br",
    "magalu": "magazineluiza.com.br",
    "ifood": "ifood.com.br",
    "uber": "uber.com",
    "airbnb": "airbnb.com.br",
    "booking": "booking.com",
    "paypal": "paypal.com",
    "stripe": "stripe.com",
    "binance": "binance.com",
    "coinbase": "coinbase.com",
    "nubank": "nubank.com.br",
    "itau": "itau.com.br",
    "bradesco": "bradesco.com.br",
    "santander": "santander.com.br",
    "bancointer": "bancointer.com.br",
    "caixa": "caixa.gov.br",
    "bb": "bb.com.br",
    "wise": "wise.com",
    "revolut": "revolut.com",
    "wikipedia": "wikipedia.org",
    "medium": "medium.com",
    "quora": "quora.com",
    "g1": "g1.globo.com",
    "uol": "uol.com.br",
    "folha": "folha.uol.com.br",
    "estadao": "estadao.com.br",
    "nytimes": "nytimes.com",
    "theverge": "theverge.com",
    "techcrunch": "techcrunch.com",
    "udemy": "udemy.com",
    "coursera": "coursera.org",
    "duolingo": "duolingo.com",
    "govbr": "gov.br",
}

FAVICON_URL = "https://www.google.com/s2/favicons"
ICON_SIZE = 64

def fetch_favicon(name: str, domain: str):
    output_path = OUTPUT_DIR / f"{name}.webp"

    if output_path.exists():
        print(f"✔ {name} já existe, pulando")
        return

    try:
        response = requests.get(
            FAVICON_URL,
            params={"sz": ICON_SIZE, "domain": domain},
            timeout=10
        )
        response.raise_for_status()

        # Converte para WebP usando Pillow
        image = Image.open(io.BytesIO(response.content))
        
        # Garante que imagens RGBA (transparência) sejam preservadas
        image.save(output_path, "WEBP", quality=80, method=6)
        
        print(f"⬇️  {name} salvo em: {output_path}")

    except Exception as e:
        print(f"❌ Erro ao processar {name}: {e}")

def main():
    print(f"📂 Destino: {OUTPUT_DIR}")
    print(f"🔽 Iniciando download e conversão para WebP ({len(SITES)} sites)...\n")
    for name, domain in SITES.items():
        fetch_favicon(name, domain)
    print("\n✅ Processo concluído!")

if __name__ == "__main__":
    main()