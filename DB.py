import serializers
import sqlite3


class Messages:
    def __init__(self):
        """Connecting to the database, creating all the tables that are needed"""
        self.connect = sqlite3.connect("MsgsData.db", check_same_thread=False)
        self.cursor = self.connect.cursor()
        with self.connect:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS UsersSuggests(
                                chat_id BIGINT,
                                username STR,
                                msg_id BIGINT,
                                group_id BIGINT,
                                id_in_group BIGINT,
                                was_forwarded INT,
                                content_type STR,
                                file_id STR,
                                caption STR)""")  # Messages from users
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS UsersReplays(
                                id_in_group BIGINT,
                                group_id BIGINT,
                                chat_id BIGINT,
                                msg_id BIGINT,
                                was_copied INT,
                                content_type STR,
                                file_id STR,
                                caption STR)""")  # Messages from group
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS UsersMsgStates(chat_id BIGINT, msg_state BIGINT)""")
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS BannedUsers(chat_id BIGINT, username STR)""")

    def add_message(self, user_suggests_data: serializers.UsersSuggestsData) -> None:
        """Adding a message from the user to the table. Accepts the necessary data about the user and chat from
        "message" dictionary. Example: message.chat.id, message.from_user.username, message. id"""
        with self.connect:
            self.cursor.execute(f"INSERT INTO UsersSuggests('chat_id', 'username', 'msg_id', 'group_id',"
                                f"'id_in_group', 'was_forwarded', 'content_type', 'file_id', 'caption')"
                                f"VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (user_suggests_data.chat_id,
                                 user_suggests_data.username,
                                 user_suggests_data.msg_id,
                                 user_suggests_data.group_id,
                                 user_suggests_data.id_in_group,
                                 user_suggests_data.was_forwarded,
                                 user_suggests_data.content_type,
                                 user_suggests_data.file_id,
                                 user_suggests_data.caption))

    # def add_message(self, user_suggests_data: serializers.UsersSuggestsData) -> None:
    #     """Adding a message from the user to the table. Accepts the necessary data about the user and chat from
    #     "message" dictionary. Example: message.chat.id, message.from_user.username, message. id"""
    #     with self.connect:
    #         self.cursor.execute(
    #             f"INSERT INTO UsersSuggests('chat_id', 'username', 'msg_id', 'group_id',"
    #             f"'id_in_group', 'was_forwarded', 'content_type', 'file_id', 'caption')"
    #             f"VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
    #             (
    #                 user_suggests_data.chat_id,
    #                 user_suggests_data.username,
    #                 user_suggests_data.msg_id,
    #                 user_suggests_data.group_id,
    #                 None,
    #                 0,
    #                 user_suggests_data.content_type,
    #                 user_suggests_data.file_id,
    #                 user_suggests_data.caption,
    #             )
    #         )

    def out_messages_to_forward(self, chat_id: int) -> list[serializers.UsersSuggestsData]:
        """Returns all messages that have not yet been forwarded to the group in a list format with tuples"""
        with self.connect:
            return self.cursor.execute("SELECT * FROM UsersSuggests WHERE chat_id=? AND was_forwarded=?",
                                       (chat_id, 0)).fetchall()

    def make_message_forwarded(self, chat_id: int, group_id: int, messages: list, emp_msgs: bool = False) -> None:
        """Marks all forwarded messages in the database"""
        with self.connect:
            id_in_group = self.get_chat_state(group_id)
            for message in messages:
                if emp_msgs:
                    id_in_group = None
                else:
                    id_in_group += 1
                self.cursor.execute("UPDATE UsersSuggests SET id_in_group=? WHERE chat_id=? AND msg_id=?",
                                    (id_in_group, chat_id, message))
                self.cursor.execute("UPDATE UsersSuggests SET was_forwarded=? WHERE id_in_group=?", (1, id_in_group))
            if not emp_msgs:
                self.set_chat_state(group_id, id_in_group)

    def out_message_info_group(self, id_in_group: int) -> serializers.UsersSuggestsData or False:
        """Returns information about any message sent by the bot in the group by message ID in main group"""
        with self.connect:
            msg = self.cursor.execute("SELECT * FROM UsersSuggests WHERE id_in_group=?", (id_in_group,)).fetchall()
            if not msg:
                return False
            return msg[0]

    def out_message_info_chat(self, chat_id: int, msg_id: int) -> serializers.UsersSuggestsData or False:
        """Returns information about any message sent by the bot in the group by message ID in user`s chat"""
        with self.connect:
            msg = self.cursor.execute(f"SELECT * FROM UsersSuggests WHERE chat_id=? AND msg_id=?",
                                      (chat_id, msg_id)).fetchall()
            if not msg:
                return False
            return msg[0]

    def out_messages_group_id(self, chat_id: int, group_id: int) -> list[serializers.UsersSuggestsData]:
        """Returns all messages from media group in chat with chat_id"""
        with self.connect:
            return self.cursor.execute("SELECT * FROM UsersSuggests WHERE chat_id=? AND group_id=?",
                                       (chat_id, group_id)).fetchall()

    def ban_user(self, chat_id: int, username: str) -> None:
        """Adds a user with a chat ID and nickname (for now, additionally, you can transfer anything)
        to the blocked list"""
        with self.connect:
            self.cursor.execute("INSERT INTO BannedUsers('chat_id', 'username') VALUES(?, ?)",
                                (chat_id, username))

    def out_banned_users(self) -> list[serializers.BannedUsersData]:
        """Returns all blocked users in a list format with tuples"""
        with self.connect:
            return self.cursor.execute("SELECT * FROM BannedUsers").fetchall()

    def del_banned_user(self, chat_id: int) -> None:
        """Unlocks the user from the chat ID specified in the message (text with the command /unban <user_id> in
        the message for the lock is formatted as for copying"""
        with self.connect:
            self.cursor.execute("DELETE FROM BannedUsers WHERE chat_id=?", (chat_id,))

    def add_reply(self, id_in_group: int, group_id: str | None, chat_id: int, content_type: str,
                  file_id: str = None, caption: str = None) -> None:
        """Adds a response message to the appropriate table, the information required for transmission can be obtained
        using the out_message_info() method and the message dictionary"""
        with self.connect:
            self.cursor.execute("INSERT INTO UsersReplays('id_in_group', 'group_id', 'chat_id', 'msg_id',"
                                "'was_copied', 'content_type', 'file_id', 'caption') VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                                (id_in_group, group_id, chat_id, None, 0, content_type, file_id, caption))

    def out_reply_info_group(self, id_in_group: int) -> serializers.UsersReplaysData or False:
        """Returns information about any reply to message forwarded by bot by its id in group"""
        with self.connect:
            msg = self.cursor.execute("SELECT * FROM UsersReplays WHERE id_in_group=?", (id_in_group,)).fetchall()
            if not msg:
                return False
            return msg[0]

    def out_reply_info_chat(self, chat_id: int, msg_id: int) -> serializers.UsersReplaysData or False:
        """Returns information about any reply to message forwarded by bot by its id in user`s chat"""
        with self.connect:
            msg = self.cursor.execute("SELECT * FROM UsersReplays WHERE chat_id=? AND msg_id=?",
                                      (chat_id, msg_id)).fetchall()
            if not msg:
                return False
            return msg[0]

    def out_replays_to_copy(self, chat_id: int) -> list[serializers.UsersReplaysData]:
        """Returns all messages that have not yet been copied to the user in a list format with tuples"""
        with self.connect:
            return self.cursor.execute("SELECT * FROM UsersReplays WHERE chat_id=? AND was_copied=?",
                                       (chat_id, 0)).fetchall()

    def make_replays_copied(self, chat_id: int, replays: list, banned_msgs=False) -> None:
        """Marks all messages from group to user with chat_id as copied in the database"""
        with self.connect:
            msg_id = self.get_chat_state(chat_id)
            for reply in replays:
                msg_id += 1
                self.cursor.execute("UPDATE UsersReplays SET was_copied=? WHERE id_in_group=?", (1, reply))
                if not banned_msgs:  # If messages was not copied, msg_id still be None
                    self.cursor.execute("UPDATE UsersReplays SET msg_id=? WHERE id_in_group=?", (msg_id, reply))
            if not banned_msgs:
                self.set_chat_state(chat_id, msg_id)

    def set_chat_state(self, chat_id: int, msg_state: int) -> None:
        """Sets id of the last message as msg_state in the chat with chat_id"""
        with self.connect:
            last_state = self.cursor.execute("SELECT * FROM UsersMsgStates WHERE chat_id=?", (chat_id,)).fetchall()
            if not last_state:
                self.cursor.execute(
                    "INSERT INTO UsersMsgStates ('chat_id', 'msg_state') VALUES(?, ?)",
                    (chat_id, msg_state),
                )
                return
            self.cursor.execute("UPDATE UsersMsgStates SET msg_state=? WHERE chat_id=?", (msg_state, chat_id))

    def get_chat_state(self, chat_id: int) -> int:
        """Returns the last message id in the chat with chat_id"""
        with self.connect:
            state = self.cursor.execute("SELECT * FROM UsersMsgStates WHERE chat_id=?", (chat_id,)).fetchall()
            if not state:
                self.cursor.execute("INSERT INTO UsersMsgStates ('chat_id', 'msg_state') VALUES(?, ?)", (chat_id, 1))
                return 1
            return state[0][-1]
