# Flask 的自動發現程序實力機制還有第三條規則:如果安裝了 python-dotenv，那麼在使用 flask run 或其他命令時會使用他自動從 .flaskenv文件和.env 文件中加載環境變量
# 安裝了 python-dotenv 時，Flask在加載環境變量的優先級是 : 手動設置的環境變量 > .env中設置的環境變量 > .flaskenv 設置的環境變量
FLASK_APP=server
# FLASK_APP=app
FLASK_DEBUG=1
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=8000
