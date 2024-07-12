import json

with open("bot_data.json", "r+") as bot_data:
    """Getting information about bot and chats etc"""
    file = json.load(bot_data)
    TOKEN = file["token"]
    main_chat_id = int(file["suggest_chat_id"])
    bot_id = int(file["sugget_bot_id"])
    channel_id = file["channel_id"]
    bot_data.close()
