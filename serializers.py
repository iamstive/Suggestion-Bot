from pydantic import BaseModel


class OddRepliesData(BaseModel):
    is_reply: bool = False
    message_id: int | None = None


class UsersSuggestsData(BaseModel):
    chat_id: int
    username: str
    msg_id: int
    group_id: int
    id_in_group: int | None = None
    was_forwarded: int = 0
    content_type: str
    file_id: str
    caption: str


class UsersReplaysData(BaseModel):
    id_in_group: int
    group_id: int
    chat_id: int
    msg_id: int
    was_copied: int
    content_type: str
    file_id: str
    caption: str


class UsersMsgStatesData(BaseModel):
    chat_id: int
    msg_state: int


class BannedUsersData(BaseModel):
    chat_id: int
    username: str
