from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputMediaPhoto, InputMediaAudio, InputMediaDocument, InputMediaVideo, ReactionTypeEmoji
import json
import asyncio
import DB


with open("texts_iamstiveschannel.json", "r+", encoding='UTF-8') as bot_text:
    """Getting all phrases bot can send"""
    data = json.load(bot_text)
    bot_text.close()


with open("bot_data.json", "r+") as bot_data:
    """Getting information about bot and chats etc"""
    file = json.load(bot_data)
    TOKEN = file["token"]
    main_chat_id = int(file["suggest_chat_id"])
    bot_id = int(file["suggest_bot_id"])
    channel_id = file["channel_id"]
    bot_data.close()


# Initialising bot, database, creating buffer with groups of messages
bot = AsyncTeleBot(TOKEN)
db = DB.Messages()
ans_groups = []


async def talk(chat_id: int, text_to_send: str, *args, reply_to_msg=None, no_sound=False) -> None:
    """Sends messages to chat with chat_id, sets id of the last message for chat with chat_id"""
    try:
        now_msg_state = db.get_chat_state(chat_id)
        db.set_chat_state(chat_id, now_msg_state + 1)
        await bot.send_message(chat_id, text_to_send.format(*args), reply_to_message_id=reply_to_msg,
                               disable_notification=no_sound, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        if '403' in str(e):
            await talk(main_chat_id, data["user_banned_bot"])


async def check_user_ban(message: {}) -> bool:
    """Checks user that sent message in banned users table. Returns False if user was banned and talks him
    about this"""
    for i in db.out_banned_users():
        if message.chat.id in i:
            if message.media_group_id not in ans_groups:
                if message.media_group_id:
                    ans_groups.append(message.media_group_id)
                await talk(message.chat.id, data["banned_user"], reply_to_msg=message.id)
            return False
    return True


async def add_odd_replays(message: {}) -> (str, int):
    """Creates dialog branch if user had been replied for own message or message from group"""
    cur_msg_info = db.out_message_info_chat(message.chat.id, message.reply_to_message.id)
    prev_msg_info = (data["suc_sent"] == message.reply_to_message.text
                     and
                     db.out_message_info_chat(message.chat.id, message.reply_to_message.id - 1))
    if cur_msg_info or prev_msg_info:  # Case for own message
        msg_info_id = (cur_msg_info or prev_msg_info)[4]
        return "additional", msg_info_id
    if db.out_reply_info_chat(message.chat.id, message.reply_to_message.id):  # Case for message form group
        return "reply", db.out_reply_info_chat(message.chat.id, message.reply_to_message.id)[0]


async def find_file_id(content_type: str, json_dict: dict) -> (str, str):
    """Returns file id if exists"""
    try:
        caption = json_dict['caption']
    except KeyError:
        caption = ''
    if content_type == 'photo':
        return json_dict[content_type][-1]['file_id'], caption
    if content_type in ["video", "audio", "sticker", "voice", "video_note", "document", "animation"]:
        return json_dict[content_type]['file_id'], caption
    if content_type == 'text':
        return content_type, json_dict[content_type]
    if content_type == 'poll':
        return content_type, ''


async def copy_messages(chat_id: int, from_chat_id: int, messages: list, not_copy: list, additional_caption: str, *args,
                        reply_to_msg: int = None, add_c_above: bool = True) -> None | bool:
    caption_from_media = messages[0][-1]
    print('tri', caption_from_media, not_copy, args)
    print(messages)
    if caption_from_media and (0 not in not_copy):
        if add_c_above:
            caption = additional_caption.format(*args) + '\n\n' + caption_from_media
        else:
            caption = caption_from_media + '\n\n' + additional_caption.format(*args)
    else:
        caption = additional_caption.format(*args)
        print('pat', *args, caption)
    for i in not_copy:
        if i != 0:
            try:
                messages.pop(int(i) - 1)
            except IndexError:
                continue
    print('heh')
    try:
        if (len(messages[0]) == 9 and messages[0][3]) or (len(messages[0]) == 8 and messages[0][1]):
            media_group = []
            ft = True
            cnt = 0
            for i in messages:
                cnt += 1
                if i[-3] == "video":
                    media_group.append(InputMediaVideo(i[-2], caption=caption, parse_mode="HTML",
                                                       show_caption_above_media=add_c_above))
                if i[-3] == "photo":
                    media_group.append(InputMediaPhoto(i[-2], caption=caption, parse_mode="HTML",
                                                       show_caption_above_media=add_c_above))
                if i[-3] == "document":
                    t_caption = ''
                    if cnt == len(messages):
                        t_caption = caption
                    media_group.append(InputMediaDocument(i[-2], caption=t_caption, parse_mode="HTML"))
                if i[-3] == "audio":
                    t_caption = ''
                    if cnt == len(messages):
                        t_caption = caption
                    media_group.append(InputMediaAudio(i[-2], caption=t_caption, parse_mode="HTML"))
                if ft:
                    ft = False
                    caption = None
            await bot.send_media_group(chat_id, media_group, reply_to_message_id=reply_to_msg)
        else:
            for message in messages:
                if message[-3] == "text":
                    await bot.send_message(chat_id, caption, reply_to_message_id=reply_to_msg, parse_mode="HTML",
                                           disable_web_page_preview=True)
                if message[-3] == "animation":
                    await bot.send_animation(chat_id, message[-2], caption=caption, reply_to_message_id=reply_to_msg,
                                             parse_mode="HTML", show_caption_above_media=add_c_above)
                if message[-3] == "photo":
                    await bot.send_photo(chat_id, message[-2], caption=caption, reply_to_message_id=reply_to_msg,
                                         parse_mode="HTML", show_caption_above_media=add_c_above)
                if message[-3] == "video":
                    await bot.send_video(chat_id, message[-2], caption=caption, reply_to_message_id=reply_to_msg,
                                         parse_mode="HTML", show_caption_above_media=add_c_above)
                if message[-3] == "audio":
                    await bot.send_audio(chat_id, message[-2], caption=caption,
                                         reply_to_message_id=reply_to_msg, parse_mode="HTML")
                if message[-3] == "sticker":
                    await talk(chat_id, caption, reply_to_msg=reply_to_msg)
                    await bot.send_sticker(chat_id, message[-2])
                if message[-3] == "voice":
                    await bot.send_voice(chat_id, message[-2], caption=caption,
                                         reply_to_message_id=reply_to_msg, parse_mode="HTML")
                if message[-3] == "video_note":
                    await talk(chat_id, caption, reply_to_msg=reply_to_msg)
                    await bot.send_video_note(chat_id, message[-2], reply_to_message_id=reply_to_msg)
                if message[-3] == "document":
                    print('alm', message)
                    await bot.send_document(chat_id, message[-2], caption=caption,
                                            reply_to_message_id=reply_to_msg, parse_mode="HTML")
                if message[-3] == "poll":
                    await talk(chat_id, caption, reply_to_msg=reply_to_msg)
                    await bot.copy_message(chat_id, from_chat_id, message[(message[4] > 3) * 2])
                caption = ''
    except Exception as e:
        if len(messages[0]) == 8:
            reply = [i[0] for i in messages]
            db.make_replays_copied(chat_id, reply, banned_msgs=True)
        else:
            reply = [i[2] for i in messages]
            db.make_message_forwarded(chat_id, main_chat_id, reply, emp_msgs=True)
        if 'USER_IS_BLOCKED' in str(e):
            await talk(main_chat_id, data["user_banned_bot"], reply_to_msg=messages[0][0])
            return True


async def cooldown_timer_forward(seconds: float, chat_id: int) -> [(), (), ...]:
    await asyncio.sleep(seconds)
    return db.out_messages_to_forward(chat_id)


async def cooldown_timer_reply(seconds: float, chat_id: int) -> [(), (), ...]:
    await asyncio.sleep(seconds)
    return db.out_replays_to_copy(chat_id)


async def reply_to_message(message):
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_id and '-' in message.text:
        msg_to_reply = db.out_message_info_group(message.reply_to_message.message_id)
        print('info')
        if not msg_to_reply:
            return
        file_info = await find_file_id(message.content_type, message.json)
        print('info_file')
        try:
            db.add_reply(message.id, message.media_group_id, msg_to_reply[0], message.content_type, file_info[0],
                         file_info[1][1:])
        except TypeError:
            db.add_reply(message.id, message.media_group_id, msg_to_reply[0], message.content_type, *file_info)
        if len(db.out_replays_to_copy(msg_to_reply[0])) == 1:
            print('letssssss goooooo')
            reply = await cooldown_timer_reply(0.25, msg_to_reply[0])
            for i in db.out_banned_users():
                if msg_to_reply[0] in i:
                    db.make_replays_copied(msg_to_reply[0], reply, banned_msgs=True)
                    return
            print('almost here!')
            fail = await copy_messages(msg_to_reply[0], main_chat_id, reply, [], data["reply_to_msg"],
                                       reply_to_msg=msg_to_reply[2], add_c_above=True)
            if not fail:
                print('aaaaasdasasaswesdsdf')
                db.make_replays_copied(msg_to_reply[0], [i[0] for i in reply])
                await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(data["reaction_reply"])])
                if msg_to_reply[2] % 7 == 0:
                    await talk(msg_to_reply[0], data["can_reply_to_msg"],
                               reply_to_msg=db.get_chat_state(msg_to_reply[0]), no_sound=True)


@bot.message_handler(commands=["start", "ban", "unban", "post"])
async def start(message):
    db.set_chat_state(message.chat.id, message.id)
    if message.chat.id != main_chat_id:
        if message.text == '/start':
            await talk(message.chat.id, data["greeting_text1"])
            await talk(message.chat.id, data["greeting_text2"], reply_to_msg=message.id + 1)
    else:
        if '/ban' in message.text and message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
            msg_info = db.out_message_info_group(message.reply_to_message.id)
            if msg_info:
                db.ban_user(msg_info[0], msg_info[1])
                try:
                    note = message.text[message.text.index(" ") + 1:]
                except ValueError:
                    note = "не указана"
                await talk(message.chat.id, data["user_banned_successful"], msg_info[1], msg_info[0], msg_info[0],
                           reply_to_msg=message.reply_to_message.id)
                await talk(msg_info[0], data["banned_user"], note)

        if '/unban' in message.text:
            try:
                l1 = len(db.out_banned_users())
                db.del_banned_user(message.text[message.text.index(" ") + 1:])
                l2 = len(db.out_banned_users())
                if l1 == l2:
                    raise Exception("User Not Found")
                await talk(message.chat.id, data["unban_user"], reply_to_msg=message.id)
                await talk(message.text[message.text.index(" ") + 1:], data["unbanned_user"])
                return
            except Exception as e:
                if e == 'User Not Found':
                    await talk(message.chat.id, data["wrong_unban_user"], reply_to_msg=message.chat.id)

        if '/post' in message.text and message.reply_to_message and message.reply_to_message.from_user.id == bot_id:
            messages_to_post = [db.out_message_info_group(message.reply_to_message.id),]
            del_params = []
            if messages_to_post[0][3]:
                messages_to_post = db.out_messages_group_id(messages_to_post[0][0], messages_to_post[0][3])
            if '-' in message.text:
                try:
                    print('adin', messages_to_post)
                    del_params = sorted(int(i) for i in set(
                        map(str, message.text[message.text.index('-') + 1:].split())
                        ) if i.isdigit())
                except ValueError or IndexError:
                    await talk(main_chat_id, data["wrong_posting"], reply_to_msg=message.id)
                    return
            print('dva', messages_to_post, del_params, messages_to_post[0][1])
            await copy_messages(channel_id, message.chat.id, messages_to_post, del_params, data["thanks_for_suggest"],
                                messages_to_post[0][1], add_c_above=False)
            await talk(main_chat_id, data["posted_successful"], reply_to_msg=message.id)


@bot.message_handler(content_types=["text", "photo", "animation", "video", "audio", "sticker", "voice", "video_note",
                                    "document", "poll"])
async def take_a_post(message):
    print(message)
    db.set_chat_state(message.chat.id, message.id)
    if message.chat.id != main_chat_id and await check_user_ban(message):
        file_info = await find_file_id(message.content_type, message.json)
        db.add_message(message.chat.id, message.from_user.first_name, message.id, message.media_group_id,
                       message.content_type, *file_info)
        if len(db.out_messages_to_forward(message.chat.id)) == 1:
            add_c = f"""<a href="t.me/{message.from_user.username}">{message.from_user.first_name}</a> """
            msgs_to_forward = await cooldown_timer_forward(0.25, message.chat.id)
            reply_info = None, None
            if message.reply_to_message:
                reply_info = await add_odd_replays(message)
                add_c = ''
                reaction = data["reaction_additional"]
                if reply_info[0] == "reply":
                    reaction = data["reaction_reply"]
                await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(reaction)])
            await copy_messages(main_chat_id, message.chat.id, msgs_to_forward, [], add_c,
                                reply_to_msg=reply_info[1])
            db.make_message_forwarded(message.chat.id, main_chat_id, [i[2] for i in msgs_to_forward])
            if not message.reply_to_message:
                await talk(message.chat.id, data["suc_sent"], reply_to_msg=msgs_to_forward[0][2], no_sound=True)
    else:
        await reply_to_message(message)


@bot.message_reaction_handler()
async def handle_y(call):
    print(call, 1)


asyncio.run(bot.polling())
