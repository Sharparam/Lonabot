from bot import Bot

with open('TOKEN', encoding='utf-8') as file:
    token = file.readline().strip()

bot = Bot('Lobot', token)

if __name__ == "__main__":
    bot.run()