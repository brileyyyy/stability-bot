import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
            with self.connection:
                return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))

    def user_exists(self, user_id):
         with self.connection:
              result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
              return bool(len(result))

    def set_token(self, user_id, token):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `token` = ? WHERE `user_id` = ?", (token, user_id,))

    def get_token(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT `token` FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            token = ""
            for row in result:
                token = str(row[0])
            return token
        
db = Database("stability.db")