import telebot
import openai

with open("config.ini", 'r') as config_file:
    telegram_token = config_file.readline()
    if telegram_token[-1] == '\n':
        telegram_token = telegram_token[:-1]
    openai_token = config_file.readline()
    if openai_token[-1] == '\n':
        openai_token = openai_token[:-1]
    my_id = int(config_file.readline())

openai.api_key = openai_token
bot = telebot.TeleBot(telegram_token, )
root_user_ids = [my_id]
allowed_user_ids = [my_id]

users_messages = {}

default_messages_content = [{"role": "system",
                             "content": "You are a helpful assistant"}, ]


@bot.message_handler(commands=['add'])
def start(message):

    if message.from_user.id not in root_user_ids:
        bot.send_message(message.from_user.id, "You don't have access to this command")
        print(message.from_user.id, "tried to connect")
        return

    allowed_user_ids.append(int(message.text.split(' ')[-1]))
    print(allowed_user_ids)
    bot.send_message(message.from_user.id, f"Successfully added new user id {allowed_user_ids[-1]}")


@bot.message_handler(commands=['remove'])
def start(message):

    if message.from_user.id not in root_user_ids:
        bot.send_message(message.from_user.id, "You don't have access to this command")
        print(message.from_user.id, "tried to connect")
        return

    try:
        allowed_user_ids.remove(int(message.text.split(' ')[-1]))
        print(allowed_user_ids)
        bot.send_message(message.from_user.id, f"Successfully removed user id {message.text.split(' ')[-1]}")
    except Exception as e:
        bot.send_message(message.from_user.id, f"Error removing user id: {e}")


@bot.message_handler(commands=['ls'])
def start(message):

    if message.from_user.id not in root_user_ids:
        bot.send_message(message.from_user.id, "You don't have access to this command")
        print(message.from_user.id, "tried to connect")
        return

    bot.send_message(message.from_user.id, f"{allowed_user_ids}")


@bot.message_handler(commands=['start'])
def start(message):

    if message.from_user.id not in allowed_user_ids:
        bot.send_message(message.from_user.id, "You don't have access to this bot")
        print(message.from_user.id, "tried to connect")
        return

    bot.send_message(message.from_user.id, "Hi! This bot is capable of using ChatGPT model")


@bot.message_handler(commands=['clear'])
def clear(message):

    if message.from_user.id not in allowed_user_ids:
        bot.send_message(message.from_user.id, "You don't have access to this bot")
        print(message.from_user.id, "tried to connect")
        return

    if message.from_user.id in users_messages:
        users_messages[message.from_user.id] = []

    print(users_messages)

    bot.send_message(message.from_user.id, "Cleared conversation")


@bot.message_handler(content_types=['text'])
def process_text_messages(message):

    if message.from_user.id not in allowed_user_ids:
        bot.send_message(message.from_user.id, f"You don't have access to this bot. "
                                               f"Ask admin to add id {message.from_user.id}")
        print(message.from_user.id, "tried to connect")
        return

    if message.from_user.id not in users_messages:
        users_messages[message.from_user.id] = default_messages_content.copy()

    users_messages[message.from_user.id].append({"role": "user", "content": message.text})
    previous_messages = users_messages[message.from_user.id]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=previous_messages
        )
    except openai.error.APIError as e:
        bot.send_message(message.from_user.id, f"APIError:{e}")
    except Exception as e:
        bot.send_message(message.from_user.id, f"Error:{e}")
        return

    users_messages[message.from_user.id].append({"role": "assistant",
                                                 "content": response["choices"][0]["message"]["content"]})

    print(users_messages)

    if len(users_messages[message.from_user.id][-1]["content"]) > 4000:
        chunks = [users_messages[message.from_user.id][-1]["content"][i:i+4000] for i in range(0, len(users_messages[message.from_user.id][-1]["content"]), 4000)]
        for chunk in chunks:
            bot.send_message(message.from_user.id, chunk)
    else:
        bot.send_message(message.from_user.id, response["choices"][0]["message"]["content"])


print("Listening...")
try:
    bot.infinity_polling(interval=0)
except Exception as e:
    print(e)
