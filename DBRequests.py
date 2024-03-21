import sqlite3


conn = sqlite3.connect('forks.db', check_same_thread=False)
cursor = conn.cursor()


class ForksData:
    def __init__(self):
        self.connect = sqlite3.connect("forks.db", check_same_thread=False)
        self.cursor = self.connect.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id STR,
        user_name STR""")

    def out_username(self, uid):
        with self.connect:
            return self.cursor.execute(f"SELECT user_name FROM 'users' WHERE user_id = {uid}").fetchone()[0]

    def add_user(self, uid, uname):
        uid = str(uid)
        with self.connect:
            if int(uid) < 0:
                uid = 'm' + uid[1:]
            self.cursor.execute("INSERT INTO users('user_id', 'user_name') VALUES(?, ?)", (uid, uname))
            self.cursor.execute(f"""CREATE TABLE u{uid}Table(time
            date DATE,
            time TIME,
            turn STR,
            message STR,
            file STR""")
            return

    def add_fork_detail(self):
        pass