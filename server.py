from flask import Flask, request , render_template, Response, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_mysqldb import MySQL
import cv2
import os
import time
import configparser
# import json

from models.de import detect,get_model, test_detect #測試
yolov5_model = get_model() #測試

# config 初始化
config = configparser.ConfigParser()
config.read('config.ini')

# Flask 初始化
app=Flask(__name__,  static_folder='static', template_folder='templates') #__name__ 代表目前執行的模組
app.secret_key = config.get('flask', 'secret_key') # 設定 flask 的密鑰secret_key。要先替 flask 設定好secret_key，Flask-Login 才能運作。

# MYSQL 資料庫初始化
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'zxcvbnm987'
app.config['MYSQL_DB'] = 'flask'
 
#mysql = MySQL(app)

# users 使用者清單 定義一個使用者清單，'Me'是帳號(或說是使用者名稱)，這個帳號的密碼是'myself'。這當然是一個簡單的設定方式。喜歡的話也可以在 Heroku Postgres 上另外做一個表單(table)，並將使用者資料存放在那邊。
users = {'Justin': {'password': '12345678'}}

# Flask-Login 初始化
login_manager = LoginManager() # 產生一個LoginManager()物件來初始化 Flask-Login
login_manager.init_app(app) # 將 flask 和 Flask-Login 綁定起來
login_manager.session_protection = "strong" # 將session_proctection調整到最強。預設是"basic"，也會有一定程度的保護，所以這行可選擇不寫上去。
login_manager.login_view = 'login' # 當使用者還沒登入，卻請求了一個需要登入權限才能觀看的網頁時，我們就先送使用找到login_view所指定的位置來。以這行程式碼為例，當未登入的使用者請求了一個需要權限的網頁時，就將他送到代表login()的位址去。我們現在還沒寫出login()這個函數，所以等等要補上。
login_manager.login_message = '請先登入才能使用此功能' # login_message是和login_view相關的設定，當未登入的使用者被送到login_view所指定的位址時，會一併跳出的訊息。

# 宣告我們要借用 Flask-Login 提供的類別UserMixin，並放在User這個物件上。但其實這裡沒有對UserMixin做出任何更動，因此下面那行程式碼用個pass就行。
class User(UserMixin):
    pass

# 做一個驗證使用者是否登入的user_loader()。下面的程式碼基本上就是確認使用者是否是在我們的合法清單users當中，若沒有，就什麼都不做。若有，就宣告一個我們剛才用UserMixin做出來的物件User()，貼上user標籤，並回傳給呼叫這個函數user_loader()的地方。
@login_manager.user_loader
def user_loader(userAccount):
    if userAccount not in users:
        return

    user = User()
    user.id = userAccount
    return user

# 做一個從flask.request驗證使用者是否登入的request_loader()。下面的程式碼基本上就是確認使用者是否是在我們的合法清單users當中，若沒有，就什麼都不做。若有，就宣告一個我們剛才用UserMixin做出來的物件User()，貼上user標籤，並回傳給呼叫這個函數request_loader()的地方。並在最後利用user.is_authenticated = request.form['password'] == users[使用者]['password']來設定使用者是否成功登入獲得權限了。若使用者在登入表單中輸入的密碼request.form['password']和我們知道的users[使用者]['password']一樣，就回傳True到user.is_authenticated上。
@login_manager.request_loader
def request_loader(request):
    userAccount = request.form.get('userAccount')
    if userAccount not in users:
        return

    user = User()
    user.id = userAccount

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[userAccount]['password']

    return user


# 使用者有沒有點擊開始偵測 #測試用
is_click = False
# 口罩偵測(test_detect)出來的值(狀態state)
test_detect_return = ""

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
            global test_detect_return
            if is_click == True:
                is_click = False
                test_detect_return = test_detect(yolov5_model,frame)[0] # 辨識完的結果
                test_detect_image = test_detect(yolov5_model,frame)[1] # 辨識完的圖片
                now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())#測試用，加時間戳
                print(f"測試偵測結果為 ==> {test_detect_return}, 偵測時間為{now_time}")
                img_file_path =f'D:\\MCUT-yolov5-to-flask\\static\\img\\detect_result\\{time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())}.jpg' # 保存圖片的路徑
                cv2.imwrite(img_file_path, test_detect_image) #保存圖片(須注意imwrite 不支持中文路徑和文件名)
                with open('detect_log.txt','a+',encoding='utf-8') as file: # a+ 打開一個文件用於讀寫。如果該文件已存在，文件指針將會放在文件的结尾。文件打開時會是追加模式。如果該文件不存在，創建新文件用於讀寫。
                    log_data=f"測試偵測結果為 ==> {test_detect_return}, 偵測時間為{now_time}, 檔案路徑為{img_file_path}\n" # add backslash n for the newline characters at the end of each line
                    file.write(log_data)

            # date_time = str(datetime.now())  #測試用，加時間戳 ref: https://ask.csdn.net/questions/7578158?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522167990655916800188519832%2522%252C%2522scm%2522%253A%252220140713.130102334.pc%255Fall.%2522%257D&request_id=167990655916800188519832&biz_id=4&utm_medium=distribute.pc_search_result.none-task-ask_topic-2~all~first_rank_ecpm_v1~rank_v31_ecpm-2-7578158-null-null.142%5Ev76%5Epc_search_v2,201%5Ev4%5Eadd_ask,239%5Ev2%5Einsert_chatgpt&utm_term=global%20cap_msmf.cpp%3A1759%20CvCapture_MSMF%3A%3AgrabFrame%20videoio%28MSMF%29%3A%20cant%20grab%20frame&spm=1018.2226.3001.4187   
            frame = detect(yolov5_model,frame) #測試用
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
@login_required
def history():
    # 顯示在歷史紀錄頁面table中的資料
    detection_history_data = [] 

    #測試資料(之後會改從資料庫裡撈)
    test_data = [["學生", "吳家豪", "with_mask", "2023-03-23 09:18:03"], 
                 ["訪客", "彭于晏", "mask_weared_incorrect", "2023-03-24 14:18:03"], 
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"], 
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"],
                 ["老師", "周杰倫", "without_mask", "2023-03-24 17:15:44"]
    ]

    # 歷史紀錄 table 的標題
    history_page_headings = ["身份", "姓名", "狀態", "偵測時間"]

    # return render_template('alert_history.html',history_page_headings=history_page_headings,python_alert_history_data=alert_history_data)
    return render_template("history.html",history_page_headings=history_page_headings, test_data=test_data)




# 關於我們(寫專案的介紹或是開發者的介紹)
@app.route("/about_us")
def about_us():
    return render_template("about_us.html")

#YoloV5只傳圖片測試用頁面
@app.route('/test_page')
@login_required
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

# 測試用頁面接收圖片的路由
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
    global test_detect_return
    detect_result = test_detect_return
    test_detect_return = ""
    # cap.release()
    # cv2.destroyAllWindows() #關閉所有opencv視窗
    data = {"trans":"沒用的資料拿來測試用而已","detect_result": detect_result}
    # data = json.dumps(data)
    print(data)
    
    return data

@app.route('/create_table')
def create_table():
    cursor = mysql.connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                    id serial UNIQUE PRIMARY KEY ,
                    school_id TEXT ,
                    user_name TEXT ,
                    email TEXT ,
                    password TEXT
                    );''')

    mysql.connection.commit()
    cursor.close()
    return "create success!!"

@app.route('/drop_table')
def drop_table():
    cursor = mysql.connection.cursor()
    cursor.execute('DROP TABLE IF EXISTS user_data')
    mysql.connection.commit()
    cursor.close()
    return "drop success!!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    userrrr = request.form['userAccount'] # userrrr 是使用者
    if (userrrr in users) and (request.form['password'] == users[userrrr]['password']):
        user = User()
        user.id = userrrr
        login_user(user)
        flash(f'{userrrr}！歡迎使用口罩辨識系統！')
        return redirect(url_for('index'))

    flash('登入失敗了...')
    return render_template('login.html')

# 登出函數
@app.route('/logout')
def logout():
    userrrr = current_user.get_id() # userrrr 是使用者
    logout_user()
    if userrrr == None:
        flash(f'您已登出！')
    else:
        flash(f'{userrrr}！歡迎下次再來！')
    return render_template('login.html')

# 使用者註冊表單
@app.route('/user_signup', methods = ['POST', 'GET'])
def user_signup():
    if request.method == 'GET':
        return render_template('signup_page.html')
     
    if request.method == 'POST':
        school_id = request.form['school_id']
        user_name = request.form['user_name']
        email = request.form['email']
        password = request.form['password']
        # cursor = mysql.connection.cursor()
        print(school_id,user_name,email,password)
        # 資料庫的東西暫時先拿掉
        # cursor.execute("INSERT INTO user_data (school_id, user_name, email, password) VALUES (%s,%s,%s,%s);",(school_id, user_name, email ,password))
        # mysql.connection.commit()
        # cursor.close()

        return f"<h1>signup success!! your name is {user_name}</h1>"

# 管理員登入表單
@app.route("/user_signin",methods=["POST"])
def user_signin():
    #從前端取得使用者的輸入
    admin_account=request.form["adminAccount"]
    # admin_password=request.form["adminPassword"]
    
    return  f"login success!! your account is {admin_account}"

@app.route('/show')
def show():
    return render_template('show.html')

# https://softwareparticles.com/stream-images-to-browser-creating-a-slideshow-in-python/
@app.route('/slideshow')
def slideshow():
    # 在gen()函數中，我們將使用yield關鍵字來返回圖像。
    return Response(gen(),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/camera')
@login_required
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