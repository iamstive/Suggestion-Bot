from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputMediaPhoto, InputMediaAudio, InputMediaDocument, InputMediaVideo, ReactionTypeEmoji
import json
import asyncio
import DB
import settings


with open("texts_iamstiveschannel.json", "r+", encoding='UTF-8') as bot_text:
    """Getting all phrases bot can send"""
    data = json.load(bot_text)
    bot_text.close()


# Initialising bot, database, creating buffer with groups of messages
bot = AsyncTeleBot(settings.TOKEN)
db = DB.Messages()
ans_groups = []


async def talk(chat_id: int, text_to_send: str, *args, reply_to_msg=None, no_sound=False) -> None:
    """Sends messages to chat with chat_id, sets id of the last message for chat with chat_id"""
    try:
        now_msg_state = db.get_chat_state(chat_id)
        db.set_chat_state(chat_id, now_msg_state + 1)
        await bot.send_message(
            chat_id,
            text_to_send.format(*args),
            reply_to_message_id=reply_to_msg,
            disable_notification=no_sound,
            parse_mode='HTML',
            disable_web_page_preview=True,
        )
    except Exception as e:  # FIXME
        if '403' in str(e):
            await talk(settings.MAIN_CHAT_ID, data["user_banned_bot"])


async def check_user_ban(message: dict) -> bool:
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


async def add_odd_replays(message: dict) -> tuple[str, int]:
    """Creates dialog branch if user had been replied for own message or message from group"""
    cur_msg_info = db.out_message_info_chat(message.chat.id, message.reply_to_message.id)
    prev_msg_info = (
        data["suc_sent"] == message.reply_to_message.text
        and
        db.out_message_info_chat(
            message.chat.id,
            message.reply_to_message.id - 1,
        )
    )
    if cur_msg_info or prev_msg_info:  # Case for own message
        msg_info_id = (cur_msg_info or prev_msg_info)[4]
        return "additional", msg_info_id
    if db.out_reply_info_chat(message.chat.id, message.reply_to_message.id):  # Case for message form group
        return "reply", db.out_reply_info_chat(message.chat.id, message.reply_to_message.id)[0]


async def find_file_id(content_type: str, json_dict: dict) -> tuple[str, str]:
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


async def copy_messages(
    chat_id: int,
    from_chat_id: int,
    messages: list,
    not_copy: list,
    additional_caption: str,
    *args,
    reply_to_msg: int = None,
    add_c_above: bool = True
) -> None | bool:
    caption_from_media = messages[0][-1]
    if caption_from_media and (0 not in not_copy):  # Speculations with captions/texts in message :)
        nki = '\n\n'
        if not additional_caption:
            nki = ''
        if add_c_above:
            caption = additional_caption.format(*args) + nki + caption_from_media
        else:
            nki = '\n'
            caption = f'<blockquote>{caption_from_media}</blockquote>' + nki + additional_caption.format(*args)
    else:
        caption = additional_caption.format(*args)

    for i in reversed(not_copy):  # Deleting messages that should not be copied
        if i != 0:
            try:
                messages.pop(int(i) - 1)
            except IndexError:
                continue

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
            db.make_message_forwarded(
                chat_id,
                settings.MAIN_CHAT_ID,
                reply,
                emp_msgs=True,
            )
        if '403' in str(e):
            await talk(
                settings.MAIN_CHAT_ID,
                data["user_banned_bot"],
                reply_to_msg=messages[0][0],
            )
            return True


async def cooldown_timer_forward(seconds: float, chat_id: int) -> list[tuple]:
    await asyncio.sleep(seconds)
    return db.out_messages_to_forward(chat_id)


async def cooldown_timer_reply(seconds: float, chat_id: int) -> list[tuple]:
    await asyncio.sleep(seconds)
    return db.out_replays_to_copy(chat_id)


async def reply_to_message(message):
    replying = (
        message.reply_to_message.from_user.id == settings.BOT_ID
        or
        db.out_reply_info_group(message.reply_to_message.id)
    )
    
    if all((
        message.reply_to_message,
        ((not message.text) or message.text[0] != '-'),
        replying,
    )):
    
        if db.out_message_info_group(message.reply_to_message.message_id):
            f = 1
            msg_to_reply = db.out_message_info_group(message.reply_to_message.message_id)
        else:
            f = 2
            msg_to_reply = db.out_reply_info_group(message.reply_to_message.id)
        if not msg_to_reply:
            return
        file_info = await find_file_id(message.content_type, message.json)
        chat_id = msg_to_reply[0] if f == 1 else msg_to_reply[2]
        db.add_reply(message.id, message.media_group_id, chat_id,
                     message.content_type, *file_info)

        if len(db.out_replays_to_copy(chat_id)) == 1:
            reply = await cooldown_timer_reply(0.1, chat_id)
            for i in db.out_banned_users():
                if chat_id in i:
                    db.make_replays_copied(chat_id, reply, banned_msgs=True)
                    return
            fail = await copy_messages(chat_id, settings.MAIN_CHAT_ID, reply, [], data["reply_to_msg"] if f == 1 else '',
                                       reply_to_msg=msg_to_reply[2] if f == 1 else msg_to_reply[3], add_c_above=True)
            if not fail:
                db.make_replays_copied(chat_id, [i[0] for i in reply])
                await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(data["reaction_reply"])])
                if msg_to_reply[2] % 7 == 0:
                    await talk(chat_id, data["can_reply_to_msg"],
                               reply_to_msg=db.get_chat_state(chat_id), no_sound=True)


@bot.message_handler(commands=["start", "ban", "unban", "post", "react", "help"])
async def start(message):
    db.set_chat_state(message.chat.id, message.id)
    if message.text == '/start':
        await talk(message.chat.id, data["greeting_text1"])
        await talk(message.chat.id, data["greeting_text2"], reply_to_msg=message.id + 1)

    if message.text == '/help':
        await talk(message.chat.id, data["general_commands"])
        if message.chat.id == settings.MAIN_CHAT_ID:
            await talk(message.chat.id, data["admin_commands"])
            
    if message.chat.id != settings.MAIN_CHAT_ID:
        if '/react' in message.text and message.reply_to_message and message.reply_to_message.from_user.id == settings.BOT_ID:
            try:
                reaction = message.text[message.text.index(" ") + 1:]
                msg_info = db.out_reply_info_chat(message.chat.id, message.reply_to_message.id)
                if not msg_info:
                    return
                msg_id = msg_info[0]
                await bot.set_message_reaction(settings.MAIN_CHAT_ID, msg_id, [ReactionTypeEmoji(reaction)], is_big=True)
                await bot.set_message_reaction(message.chat.id, message.reply_to_message.id,
                                               [ReactionTypeEmoji(reaction)])
            except:
                await talk(message.chat.id, data["failed_set_reaction"], reply_to_msg=message.id, no_sound=True)

    else:
        if '/ban' in message.text and message.reply_to_message and message.reply_to_message.from_user.id == settings.BOT_ID:
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

        if '/post' in message.text and message.reply_to_message and message.reply_to_message.from_user.id == settings.BOT_ID:
            messages_to_post = [db.out_message_info_group(message.reply_to_message.id), ]
            del_params = []
            if messages_to_post[0][3]:
                messages_to_post = db.out_messages_group_id(messages_to_post[0][0], messages_to_post[0][3])
            try:
                add_c = ''
                if '-' in message.text:
                    del_params = sorted(int(i) for i in set(
                        map(str, message.text[message.text.index('-') + 1:
                                              message.text.index('!') if '!' in message.text else -1].split()))
                                        if i.isdigit())
                if '!' in message.text:
                    add_c = message.text[message.text.index('!') + 1:] + '\n\n'
            except ValueError or IndexError:
                await talk(settings.MAIN_CHAT_ID, data["wrong_posting"], reply_to_msg=message.id)
                return
            await copy_messages(settings.CHANNEL_ID, message.chat.id, messages_to_post, del_params, add_c +
                                data["thanks_for_suggest"], messages_to_post[0][1], add_c_above=False)
            await talk(settings.MAIN_CHAT_ID, data["posted_successful"], reply_to_msg=message.id)

        if '/react' in message.text[:6] and message.reply_to_message and message.reply_to_message.from_user.id == settings.BOT_ID:
            try:
                msg_info = db.out_message_info_group(message.reply_to_message.id)
                if not msg_info:
                    return
                reaction = message.text[message.text.index(" ") + 1:]
                await bot.set_message_reaction(msg_info[0], msg_info[2], [ReactionTypeEmoji(reaction)], is_big=True)
                await bot.set_message_reaction(settings.MAIN_CHAT_ID, message.reply_to_message.id, [ReactionTypeEmoji(reaction)])
            except:
                await talk(message.chat.id, data["failed_set_reaction"], reply_to_msg=message.id, no_sound=True)


@bot.message_handler(content_types=["text", "photo", "animation", "video", "audio", "sticker", "voice", "video_note",
                                    "document", "poll"])
async def take_a_post(message):
    """Copies messages from user to main group"""
    db.set_chat_state(message.chat.id, message.id)
    if message.chat.id != settings.MAIN_CHAT_ID and await check_user_ban(message):  # Finding file id`s in tg if exists
        file_info = await find_file_id(message.content_type, message.json)
        db.add_message(message.chat.id, message.from_user.first_name, message.id, message.media_group_id,
                       message.content_type, *file_info)

        if len(db.out_messages_to_forward(message.chat.id)) == 1:
            add_c = f'<a href="t.me/{message.from_user.username}">{message.from_user.first_name}</a>'
            msgs_to_forward = await cooldown_timer_forward(0.1, message.chat.id)
            reply_id = None
            failed_copy = True

            if message.reply_to_message:  # Making beautiful reply if it needs
                try:
                    reply_type, reply_id = await add_odd_replays(message)
                    add_c = ''
                    reaction = data["reaction_additional"]
                    if reply_type == "reply":
                        reaction = data["reaction_reply"]
                    await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(reaction)])
                except TypeError:
                    reply_id = None

            try:
                await copy_messages(settings.MAIN_CHAT_ID, message.chat.id, msgs_to_forward, [], add_c, reply_to_msg=reply_id)
                failed_copy = False
                await talk(message.chat.id, data["suc_sent"], reply_to_msg=msgs_to_forward[0][2], no_sound=True)
            finally:
                db.make_message_forwarded(message.chat.id, settings.MAIN_CHAT_ID, [i[2] for i in msgs_to_forward],
                                          emp_msgs=failed_copy)
    else:
        await reply_to_message(message)


asyncio.run(bot.polling())
