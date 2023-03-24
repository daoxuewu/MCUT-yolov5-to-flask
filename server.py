from flask import Flask, request , render_template, Response, url_for
#from flask_mysqldb import MySQL
import cv2
import os
import time

from models.de import detect,get_model #測試
yolov5_model = get_model() #測試

app=Flask(__name__,  static_folder='static', template_folder='templates') #__name__ 代表目前執行的模組



# 網頁串流
def gen_frames():
    # 選擇第1隻攝影機
    cap = cv2.VideoCapture(0)

    # 檢查視頻是否打開
    if not cap.isOpened():
        raise Exception("Could not open video file")
    
    while True:
        # 先從 camera 擷取一幀又一幀的影像 Capture frame-by-frame
        success, frame = cap.read()
        
        # 檢查視頻幀是否讀取成功 if frame is read correctly success(ret) is True
        if not success:
            print("Can't not receive frame")
            break
        else: 
            # print(f"尚未通過偵測的frame{frame}") #測試用
            frame = detect(yolov5_model,frame) #測試用
            # print(f"測試用的frame{frame}")  #測試用
            # 因為opencv讀取的圖片並非jpeg格式，因此要用motion JPEG模式需要先將圖片轉碼成jpg格式圖片
            success, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # 使用generator函數輸出視頻流， 每次請求輸出的content類型是image/jpeg
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release() #釋放視頻文件(攝影機)
    cv2.destroyAllWindows() #關閉所有opencv視窗

# sildeShow用的生成函式
def gen():
    i = 0

    while True:
        # 圖像將每 5 秒傳輸到客戶端。
        time.sleep(2)
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

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'zxcvbnm987'
app.config['MYSQL_DB'] = 'flask'
 
#mysql = MySQL(app)

@app.route("/") #透過 decorater 定義路由並以函式為基礎提供附加功能
@app.route("/index")
def index():
    # jinja2模板
    return render_template("index.html") #函式回傳的內容

# 讓使用者登入後快速開始的頁面
@app.route("/quick_start")
def quick_start():
    return render_template("quick_start.html")

# 讓使用者登入後查看歷史紀錄的頁面
@app.route("/history")
def history():
    # 顯示在歷史紀錄頁面table中的資料
    alert_history_data = [] 

    #測試資料(之後會改從資料庫裡撈)
    test_data = [["學生", "吳家豪", "with_mask", "2023-03-24 14:18:03"], 
                 ["學生", "彭于晏", "mask_weared_incorrect", "2023-03-24 14:18:03"], 
                 ["學生", "周杰倫", "without_mask", "2023-03-24 14:18:03"], 
                 ["學生", "林俊傑", "with_mask", "2023-03-24 14:18:03"]
    ]

    # 歷史紀錄 table 的標題
    history_page_headings = ["身份", "姓名", "狀態", "偵測時間"]

    # return render_template('alert_history.html',history_page_headings=history_page_headings,python_alert_history_data=alert_history_data)
    return render_template("history.html",history_page_headings=history_page_headings, python_alert_history_data=test_data)




# 關於我們(寫專案的介紹或是開發者的介紹)
@app.route("/about_us")
def about_us():
    return render_template("about_us.html")

#YoloV5只傳圖片測試用頁面
@app.route('/test_page')
def test_page():
   return render_template('test_page.html')

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

@app.route('/login_page')
def login_page():
    return render_template('login_page.html')
 
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

        return f"signup success!! your name is {user_name}"

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
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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