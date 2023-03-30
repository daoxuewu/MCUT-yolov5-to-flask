# 彭彭版本
import mysql.connector
import sys

#連線到資料庫
con = mysql.connector.connect(
    user="root",
    password="zxcvbnm987",
    host="localhost",
    database="my_db"
)

print("Opened database successfully")

try:
    #讀取圖片檔案
    fp = open("./123.jpg")
    test_img = fp.read()
    fp.close()
except IOError as e:
    print (f"Error {e.args[0]} {e.args[1]}")
    sys.exit(1)


# 要放入資料庫的變數
stu_id = 6
name = "家豪"

# 建立 cursor 物件 (資料指標)
cursor=con.cursor()
#注意使用Binary()函式來指定儲存的是二進位制
cursor.execute("INSERT INTO product SET imgs='%s'" % mysql.Binary(test_img))
# cursor.execute("INSERT INTO product(id, name) VALUES(%s, %s)",(stu_id, name))

# # 增加欄位 
# cursor.execute("ALTER TABLE product ADD imgs BLOB;")
# print("ADD 1 column of data")

con.commit()

# close database connect
con.close()