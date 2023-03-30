from flask import Flask, request , render_template, Response, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mysqldb import MySQL
import cv2
import os
import time
from datetime import datetime
import configparser
# import json

from models.de import detect,get_model, test_detect #測試
yolov5_model = get_model() #測試

# config 初始化
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Flask 初始化 Create a Flask Instance
app=Flask(__name__,  static_folder='static', template_folder='templates') #__name__ 代表目前執行的模組
app.secret_key = config.get('flask', 'secret_key') # 設定 flask 的密鑰secret_key。要先替 flask 設定好secret_key，Flask-Login 才能運作。 How to generate good secret keys(可以參考官方連結):https://flask.palletsprojects.com/en/2.2.x/quickstart/#sessions

# MYSQL 資料庫初始化
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'zxcvbnm987'
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)

# users 使用者清單 定義一個使用者清單，'Justin'是帳號(或說是使用者名稱)，這個帳號的密碼是'12345678'。這當然是一個簡單的設定方式。喜歡的話也可以在 Heroku Postgres 上另外做一個表單(table)，並將使用者資料存放在那邊。
users = {'Justin': {'password': '12345678'}} # 用來測試的一筆假資料

# Flask-Login 初始化
login_manager = LoginManager() # 產生一個LoginManager()物件來初始化 Flask-Login
login_manager.init_app(app) # 將 flask 和 Flask-Login 綁定起來(讓flask認識flask-login)，app 即為 flask object
login_manager.session_protection = "strong" # 將session_proctection調整到最強。預設是"basic"，也會有一定程度的保護，所以這行可選擇不寫上去。
login_manager.login_view = 'login' # 當使用者還沒登入，卻請求了一個需要登入權限才能觀看的網頁時，我們就先送使用找到login_view所指定的位置來。以這行程式碼為例，當未登入的使用者請求了一個需要權限的網頁時，就將他送到代表login()的位址去。我們現在還沒寫出login()這個函數，所以等等要補上。
login_manager.login_message = '請先登入才能使用此功能' # login_message是和login_view相關的設定，當未登入的使用者被送到login_view所指定的位址時，會一併跳出的訊息。

# 宣告我們要借用 Flask-Login 提供的類別UserMixin，並放在User這個物件上。但其實這裡沒有對UserMixin做出任何更動，因此下面那行程式碼用個pass就行。
class User(UserMixin):
    """
    只是單純的繼承官方所提供的 UserMixin 而以 如果我們希望可以做更多判斷，
    如is_administrator也可以從這邊來加入 
    """
    pass

# 下面的程式碼基本上就是上面初始化完的login_manager做為裝飾器來包裝驗證使用者是否登入的user_loader()。確認使用者是否是在我們的合法清單users當中，若沒有，就什麼都不做回傳None。若有，就宣告一個我們剛才用UserMixin做出來的物件User()，貼上user(使用者)標籤，並回傳給呼叫這個函數user_loader()的地方。
@login_manager.user_loader
def user_loader(userAccount):
    """  
    透過這邊的設置讓flask_login可以隨時取到目前的使用者id   
    :param email:官網此例將email當id使用，賦值給予user.id
    ( 我把email 改成userAccount)    
    """
    #根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
    cursor = mysql.connection.cursor()
    # 檢查會員集合中是否有相同email的文件資料
    # print(f"""SELECT *FROM userdata WHERE email = '%s' """ %(email,))
    cursor.execute(f"""SELECT * FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    email_result = cursor.fetchall() # 所有使用者的email
    # if (email_result == ()) or (email_result == None):
    #     flash('請確認帳號是否輸入錯誤')
    #     return
    print(f"user_loader email_result == > {email_result}")

    mysql.connection.commit()
    # 關閉 cursor
    cursor.close()

    if userAccount not in email_result[0]: # 我把 email 改成 userAccount
        return

    user = User()
    user.id = userAccount
    return user

# 做一個從flask.request驗證使用者是否登入的request_loader()。下面的程式碼基本上就是確認使用者是否是在我們的合法清單users當中，若沒有，就什麼都不做。若有，就宣告一個我們剛才用UserMixin做出來的物件User()，貼上user標籤，並回傳給呼叫這個函數request_loader()的地方。並在最後利用user.is_authenticated = request.form['password'] == users[使用者]['password']來設定使用者是否成功登入獲得權限了。若使用者在登入表單中輸入的密碼request.form['password']和我們知道的users[使用者]['password']一樣，就回傳True到user.is_authenticated上。
@login_manager.request_loader
def request_loader(request):
    userAccount = request.form.get('userAccount') #userAccount 可以改成 email
    
    #根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
    cursor = mysql.connection.cursor()
    # 檢查會員集合中是否有相同email的文件資料
    # print(f"""SELECT *FROM userdata WHERE email = '%s' """ %(email,))
    cursor.execute(f"""SELECT * FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。

    email_result = cursor.fetchall() # 所有使用者的email
    # if (email_result == ()) or (email_result == None):
    #     flash('請確認帳號是否輸入錯誤')
    #     return
    print(f"request_loader email_result == > {email_result}")

    cursor.execute(f"""SELECT password FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    password_result = cursor.fetchone() # 該使用者的密碼
    print(f"request_loader password_result == > {password_result}")

    if (password_result == ()) or (password_result == None):
        return

    mysql.connection.commit()
    # 關閉 cursor
    cursor.close()

    if userAccount not in email_result[0]:
        return

    user = User()
    user.id = userAccount

    print(request.form['password'])
    # print(users[userAccount]['password'])
    print(password_result)
    print(request.form['password'] == password_result)

    if (request.form['password'] != password_result[0]):
        return


    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == password_result

    return user


# 使用者有沒有點擊開始偵測 #測試用
is_click = False
# 口罩偵測(test_detect)出來的值(狀態state)
global_detect_return = ""
# 存檔的圖片路徑
global_img_path = ""
# 偵測圖片當下的時間
global_now_time = ""

# 網頁串流
def gen_frames():
    # 選擇第1隻攝影機 capture
    cap = cv2.VideoCapture(0)

    # 檢查視頻是否打開
    if not cap.isOpened():
        raise Exception("Could not open video file")

    while True:
        # 先從 camera 擷取一幀又一幀的影像 Capture frame-by-frame 
        # read函式其實是grab和retrieve函式的結合, grab函式 捕獲下一幀, retrieve函式 對該幀進行解碼
        retval, frame = cap.read()
        
        # 檢查視頻幀是否讀取成功 if frame is read correctly retval(return value type 為 bool) is True
        if not retval:
            # print("Can't not receive frame")
            print("Error grabbing frame from movie!")
            break
        else:
            global is_click
            global global_detect_return
            global global_img_path
            global global_now_time
            if is_click == True:
                is_click = False
                global_detect_return = test_detect(yolov5_model,frame)[0] # 辨識完的結果
                test_detect_image = test_detect(yolov5_model,frame)[1] # 辨識完的圖片
                now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())#測試用，加時間戳
                print(f"測試偵測結果為 ==> {global_detect_return}, 偵測時間為{now_time}")
                global_now_time = now_time

                # python 抓相對路徑 ref: https://towardsthecloud.com/get-relative-path-python
                absolute_path = os.path.dirname(__file__)
                relative_path = f'static\img\detect_result\{time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())}.jpg'
                img_path = os.path.join(absolute_path, relative_path) # 絕對路徑
                global_img_path = relative_path # 保存圖片的路徑(存相對路徑)

                cv2.imwrite(img_path, test_detect_image) #保存圖片(須注意imwrite 不支持中文路徑和文件名)
                # with open('detect_log.txt','a+',encoding='utf-8') as file: # a+ 打開一個文件用於讀寫。如果該文件已存在，文件指針將會放在文件的结尾。文件打開時會是追加模式。如果該文件不存在，創建新文件用於讀寫。
                #     log_data=f"測試偵測結果為 ==> {global_detect_return}, 偵測時間為{now_time}, 檔案絕對路徑為{img_path}\n" # add backslash n for the newline characters at the end of each line
                #     file.write(log_data)



            # date_time = str(datetime.now())  #測試用，加時間戳 ref: https://ask.csdn.net/questions/7578158?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522167990655916800188519832%2522%252C%2522scm%2522%253A%252220140713.130102334.pc%255Fall.%2522%257D&request_id=167990655916800188519832&biz_id=4&utm_medium=distribute.pc_search_result.none-task-ask_topic-2~all~first_rank_ecpm_v1~rank_v31_ecpm-2-7578158-null-null.142%5Ev76%5Epc_search_v2,201%5Ev4%5Eadd_ask,239%5Ev2%5Einsert_chatgpt&utm_term=global%20cap_msmf.cpp%3A1759%20CvCapture_MSMF%3A%3AgrabFrame%20videoio%28MSMF%29%3A%20cant%20grab%20frame&spm=1018.2226.3001.4187   
            frame = detect(yolov5_model,frame) # 辨識圖片有無口罩，整個專案的核心功能 ref: https://github.com/Transformer-man/yolov5-flask
            # # 因為opencv讀取的圖片並非jpeg格式，因此要用motion JPEG模式需要先將圖片轉碼成jpg格式圖片
            retval, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # # 使用generator函數輸出視頻流， 每次請求輸出的content類型是image/jpeg
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
    # When everything done, release the capture
    cap.release() #釋放視頻文件(攝影機)
    cv2.destroyAllWindows() #關閉所有opencv視窗

# sildeShow用的生成函式
def gen():
    i = 0

    while True:
        # 圖像將每 5 秒傳輸到客戶端。
        time.sleep(5)
        images = get_all_images()
        image_name = images[i]
        im = open("static\\img\\train\\" + image_name, 'rb').read()
        # im = open("D:\\明志專題訓練影像\\" + image_name, 'rb').read()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + im + b'\r\n')
        i += 1
        if i >= len(images):
            i = 0

def get_all_images():
    image_folder = 'D:\\mcut_project\\static\\img\\train'
    # image_folder = {{ url_for('static', filename='img\\train') }}
    images = [img for img in os.listdir(image_folder)
              if img.endswith(".jpg") or
              img.endswith(".jpeg") or
              img.endswith("png")]
    return images

# 首頁
@app.route("/") #透過 decorater 定義路由並以函式為基礎提供附加功能
@app.route("/index")
def index():
    # jinja2模板
    return render_template("index.html") #函式回傳的內容


# 讓使用者登入後查看歷史紀錄的頁面
@app.route("/history")
@login_required # 這個裝飾器包裝起來的view就意謂著必需是登入狀態才能進入，否則你就是會被引導回login這個view。
def history():
    
    # 取得使用者的帳號(email)
    userAccount = current_user.get_id()

    # 根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
    cursor = mysql.connection.cursor()
    cursor.execute(f'SELECT * FROM history WHERE email = "{userAccount}"')
    history_data = cursor.fetchall()
    # print(f'history_data ==> {history_data}')
    print("")
    mysql.connection.commit()
    cursor.close()

    # 顯示在歷史紀錄頁面table中的資料
    detection_history_data = [] 
    # 下面的 for loop 是為了移除掉 primary key(id) 的資料
    for data in history_data:
        detection_history_data.append((data[1],data[2],data[3],str(data[4]),data[5]))

    # #測試資料(之後會改從資料庫裡撈)
    # test_data = [["學生", "吳家豪", "with_mask", "2023-03-23 09:18:03"], 
    #              ["訪客", "彭于晏", "mask_weared_incorrect", "2023-03-24 14:18:03"], 
    #              ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"], 
    #              ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
    #              ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
    #              ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"]
    # ]
    

    # 歷史紀錄 table 的標題
    history_page_headings = ["姓名", "帳號", "狀態", "偵測時間","截圖"]

    return render_template("history.html",history_page_headings=history_page_headings, detection_history_data=detection_history_data)

def return_img_stream(img_local_path):
    """
    工具函数:
    获取本地图片流
    :param img_local_path:文件单张图片的本地绝对路径
    :return: 图片流
    reference : https://blog.csdn.net/xyy731121463/article/details/107123635
    """
    import base64
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream

@app.route("/show_img/static/img/detect_result/<img_path>/") 
def show_img(img_path):
    print(f'img == >{img_path}')
    stream_path = 'static/img/detect_result/' + img_path
    img_stream = return_img_stream(stream_path)
    return render_template('show_img.html', img_stream=img_stream)

# 關於我們(寫專案的介紹或是開發者的介紹)
@app.route("/about_us")
def about_us():
    return render_template("about_us.html")

#YoloV5只傳圖片測試用頁面
@app.route('/test_page')
@login_required # 這個裝飾器包裝起來的view就意謂著必需是登入狀態才能進入，否則你就是會被引導回login這個view。
def test_page():
   return render_template('test_page.html')

#測試影像串流的頁面
@app.route('/test_stream', methods=["POST", "GET"])
def test_stream():
    return render_template("test_stream.html")

#測試自己寫一個video_feed
@app.route('/test_video_feed')
def test_video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

# 測試用頁面接收圖片的路由 ref: https://github.com/Transformer-man/yolov5-flask
class_names = [c.strip() for c in open(r'cam/coco.names').readlines()]
file_name = ['jpg','jpeg','png']
@app.route('/get_image', methods= ['POST'])
def get_image():
    image = request.files["images"]
    print(f'image:{image}')
    image_name = image.filename
    image.save(os.path.join(os.getcwd(), image_name))
    if image_name.split(".")[-1] in file_name:
        img = cv2.imread(image_name)
        img = detect(yolov5_model,img)
        _, img_encoded = cv2.imencode('.jpg', img)
        response = img_encoded.tobytes()
        os.remove(image_name)
        try:
            return Response(response=response, status=200, mimetype='image/jpg')
        except:
            return render_template('test_page.html')

# 按下開始偵測後會打到這個路由
@app.route('/detect_mask', methods= ['POST'])
def detect_mask():
    # 前端傳過來的資料
    data = request.form.get("mydata")

    print(f'前端傳來的資料是 ==> {data}')
    # cap = cv2.VideoCapture(0)

    # # 檢查視頻是否打開
    # if not cap.isOpened():
    #     raise Exception("Could not open video file")
    
    if data == "點擊按扭了":
        global is_click
        is_click = True
        # ret,frame = cap.read()
        # detect_result=test_detect(yolov5_model,frame)
    #     print(f'偵測結果為 == > {detect_result}')

    time.sleep(3)
    global global_detect_return
    global global_img_path
    global global_now_time
    detect_result = global_detect_return
    img_path = global_img_path
    now_time = global_now_time
    global_detect_return = ""
    # cap.release()
    # cv2.destroyAllWindows() #關閉所有opencv視窗
    data = {"trans":"沒用的資料拿來測試用而已","detect_result": detect_result}
    # data = json.dumps(data)
    print(f'回傳給前端的資料{data}')

    # 取得使用者的帳號(email)
    userAccount = current_user.get_id()
    # 根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
    cursor = mysql.connection.cursor()
    cursor.execute(f"""SELECT user_name FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    user_name = cursor.fetchone()[0] # 該使用者的名字
    # 把資料放進資料庫(偵測的歷史紀錄)
    cursor.execute("INSERT INTO history (user_name, email, state, detect_time, img_path) VALUES (%s,%s,%s,%s,%s);",(user_name, userAccount , detect_result, now_time, img_path))
    mysql.connection.commit()
    cursor.close()


    return data

@app.route('/create_table')
@login_required
def create_table():
    cursor = mysql.connection.cursor()

    # 使用者資料
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                    id serial UNIQUE PRIMARY KEY ,
                    user_name TEXT ,
                    email TEXT ,
                    password TEXT
                    );''')
    
    # 偵測的歷史紀錄
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                id serial UNIQUE PRIMARY KEY ,
                user_name TEXT ,
                email TEXT ,
                state TEXT ,
                detect_time timestamp ,
                img_path TEXT
                );''')

    # # 舊的版本(有學號)
    # cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
    #             id serial UNIQUE PRIMARY KEY ,
    #             school_id TEXT ,
    #             user_name TEXT ,
    #             email TEXT ,
    #             password TEXT
    #             );''')

    mysql.connection.commit()
    cursor.close()
    return "create success!!"

@app.route('/drop_table')
@login_required
def drop_table():
    cursor = mysql.connection.cursor()
    # cursor.execute('DROP TABLE IF EXISTS history') #要用時再拿掉註解
    mysql.connection.commit()
    cursor.close()
    return "drop success!!"

# 登入函數
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    #從前端取得使用者的輸入
    userAccount = request.form['userAccount'] # userAccount 是使用者輸入的帳號
    
    #根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
    cursor = mysql.connection.cursor()
    # 檢查會員集合中是否有相同email的文件資料
    # print(f"""SELECT *FROM userdata WHERE email = '%s' """ %(email,))
    cursor.execute(f"""SELECT * FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    email_result = cursor.fetchall() # 所有使用者的email
    print(f"email_result == > {email_result}")

    cursor.execute(f"""SELECT password FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    password_result = cursor.fetchone() # 該使用者的密碼
    print(f"password_result == > {password_result}")

    cursor.execute(f"""SELECT user_name FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
    user_name = cursor.fetchone() # 該使用者的名字
    print(f"user_name == > {user_name}")

    if (email_result == ()) or (password_result == None) or (user_name == None):
        mysql.connection.commit()
        # 關閉 cursor
        cursor.close()
        flash('登入失敗了...')
        return render_template('login.html')
    
    # 使用者(user)登入驗證帳號密碼，實務上會從資料庫中取回該帳號使用者並驗證密碼是否正確
    if (userAccount in email_result[0]) and (request.form['password'] == password_result[0]):
        # 實作User類別
        user = User()
        # 設置id就是使用者帳號(email)
        user.id = userAccount 
        # 透過login_user來記錄user_id, 在經過login_user(user)之後，後面的應用就都可以利用current_user來取得用戶資訊 ref: https://hackmd.io/@shaoeChen/ryvr_ly8f?type=view#login_user
        login_user(user)
        flash(f'{user_name[0]}！歡迎使用口罩辨識系統！')
        mysql.connection.commit()
        # 關閉 cursor
        cursor.close()
        # 登入成功，轉址
        return redirect(url_for('index'))

    mysql.connection.commit()
    # 關閉 cursor
    cursor.close()
    flash('登入失敗了...')
    return render_template('login.html')

# 登出函數
@app.route('/logout')
def logout():
    userAccount = current_user.get_id() # 在經過login_user(user)之後，後面的應用就都可以利用current_user來取得用戶資訊
    logout_user()
    if userAccount == None:
        flash(f'您已登出！')
    else:
        #根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
        cursor = mysql.connection.cursor()
        cursor.execute(f"""SELECT user_name FROM user_data WHERE email = '{userAccount}'""") #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
        user_name = cursor.fetchone()[0] # 該使用者的名字
        mysql.connection.commit()
        # 關閉 cursor
        cursor.close()
        print(f'"{user_name}"歡迎下次再來！') # 印給開發人員看
        flash(f'"{user_name}"歡迎下次再來！') # 顯示在前端給使用者看
    return redirect(url_for('index'))
    # return render_template('index.html')


# 使用者註冊表單
@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
     
    if request.method == 'POST':
        # school_id = request.form['school_id']
        user_name = request.form['user_name']
        email = request.form['email']
        password = request.form['password']
        #根據接收到的資料和資料互動，初始化一個可以執行指令的cursor() (資料指標)
        cursor = mysql.connection.cursor()
        print(user_name,email,password)
        # 檢查會員集合中是否有相同email的文件資料
        # print(f"""SELECT *FROM userdata WHERE email = '%s' """ %(email,))
        cursor.execute(f"""SELECT * FROM user_data WHERE email = '{email}' """) #cursor.execute 執行資料庫的操作或是查詢動作。一次僅操作一筆資料。
        
        email_result = cursor.fetchall()

        if email_result != ():   #非(取反) ! 本來是true變成flase; 本來是flase變成true !=就是不等於
            flash('電子郵件已經被註冊過了')
            return redirect("/signup")
        
        
        # 把資料放進資料庫，完成註冊
        cursor.execute("INSERT INTO user_data (user_name, email, password) VALUES (%s,%s,%s);",(user_name, email ,password))
        mysql.connection.commit()
        # 關閉 cursor
        cursor.close()
        flash(f'"{user_name}"恭喜註冊成功，登入可以啟用更多功能喔!')
        return render_template('login.html')



# https://softwareparticles.com/stream-images-to-browser-creating-a-slideshow-in-python/
@app.route('/slideshow')
def slideshow():
    # 在gen()函數中，我們將使用yield關鍵字來返回圖像。
    return Response(gen(),mimetype='multipart/x-mixed-replace; boundary=frame')

# 使用者查看攝影機即時串流的頁面
@app.route('/camera')
def camera():
    return render_template('camera.html')

# 返回video streaming response
@app.route('/video_feed')
def video_feed():

    # 生成視頻流，使用的ContentType是multipart/x-mixed-replace，並且每一段數據用'--frame'來做分隔
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80,debug=True,threaded=True) #開發階段使用

#     # app.run(host='0.0.0.0',port=80)