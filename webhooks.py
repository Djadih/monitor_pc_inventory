from discord_webhook import DiscordWebhook
import configparser

parser = configparser.ConfigParser()
parser.read("config.ini")
url = parser["DISCORD"]["webhook_url"]


def send_discord(message, isNew):
    webhook = DiscordWebhook(url=url, content=message)
    if isNew:
        with open("new.jpg", "rb") as f:
            webhook.add_file(file=f.read(), filename='NEW.jpg')
    webhook.execute()
