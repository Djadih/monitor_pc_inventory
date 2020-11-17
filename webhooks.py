from discord_webhook import DiscordWebhook
import configparser

parser = configparser.ConfigParser()
parser.read("config.ini")
url = parser["DISCORD"]["webhook_url"]


def send_discord(message):
    webhook = DiscordWebhook(url=url, content=message)
    webhook.execute()
