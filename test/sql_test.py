import sqlite3

conn = sqlite3.connect('user.db')
cursor = conn.cursor()

# cursor.execute('DROP TABLE IF EXISTS users')
# cursor.execute('CREATE TABLE IF NOT EXISTS users('
#                'id INTEGER UNIQUE PRIMARY KEY, '
#                'name TEXT, '
#                'email TEXT, '
#                'password TEXT)')

# insert_query = 'INSERT INTO users VALUES(?, ?, ?, ?)'

# users = []

# users.append((None, '吳家豪', 'U08157006@o365.mcut.edu.tw', '123456'))
# users.append((None,'江一折', 'U08157XXX@o365.mcut.edu.tw', '123456'))
# users.append((None, '林承旭', 'U08157XXX@o365.mcut.edu.tw', '123456'))

# cursor.executemany(insert_query, users)

# 插入資料
# cursor.execute("INSERT INTO userdata (user_name, user_id , updated_time , case_status ,case_id , email ,password) VALUES (%s, %s, %s ,%s ,%s ,%s ,%s);", ("李佳琳Charlene", "U686b19963641b30cab0ed6f39d44398c","2022-03-09 09:45:58","1","fe80::64df:99ba:e0e6:c565%5","aaa@gmail.com","666666cs"))
# print("Insert 1 row of data")

# 更新資料
# cursor.execute("UPDATE userdata SET case_status = %s WHERE email = %s;", ("0", "a@gmail.com"))
# print("Updated 1 row of data")

# 刪除資料
# cursor.execute("DELETE FROM users WHERE id = ? ;", ("2",))
# print("Deleted 1 row of data")

# 增加欄位 
# cursor.execute("ALTER TABLE userdata ADD phoneNumber varchar(20);")
# print("ADD 1 column of data")

# for row in cursor.execute('SELECT * FROM users'):
#     print(row)

cursor.execute(f"SELECT * FROM users")
result = cursor.fetchall()
# print(result)

for row in result:
    print(row)

conn.commit()
conn.close()