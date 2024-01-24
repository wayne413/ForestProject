from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import os
import base64
import secrets
from datetime import datetime
import io
from PIL import Image
import cv2
import face_recognition
import pickle
import numpy as np
import time
from sqlalchemy import create_engine, select
from sqlalchemy.orm import session
import pymysql

# 資料庫參數設定
db_settings = {
    "host": "localhost",
    "port": 3306,
    "user": "test",
    "password": "12345678",
    "db": "topics",
    "charset": "utf8",
}

# 取得啟動文件資料夾路徑
pjdir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# -------------資料庫設定---------------#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:12345678@localhost/Topics'
# 隨機設定密碼
app.config['SECRET_KEY'] = secrets.token_hex(16)


app.config['SERVER_NAME'] = 'localhost:5000'
app.config['APPLICATION_ROOT'] = 'app'
app.config['PREFERRED_URL_SCHEME'] = 'http'

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
# -------------------------------------#

# ------------資料庫Table建置-----------#


class UserRegister(db.Model):
    """資料庫紀錄"""
    __tablename__ = 'UserRegisters'
    number = db.Column(db.String(9), unique=True,
                       nullable=False, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    signup_time = db.Column(db.DateTime, default=datetime.utcnow)
    captured_image = db.Column(db.LargeBinary)
    encode_data = db.Column(db.LargeBinary)

    def __repr__(self):
        return 'ID:%d, Username:%s' % (self.id, self.username)


# 創建表格（如果還不存在）
with app.app_context():
    db.create_all()
# --------------------------------------#

# -----------------------------------------註冊網頁---------------------------------------------#


@app.route('/register', methods=['GET', 'POST'])
def register():
    error1 = False
    error2 = False
    error3 = False
    if request.method == 'POST':
        number = request.form['number']
        username = request.form['username']
        capturedImageData = request.form['capturedImageData']
        signup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 判斷是否有輸入
        if not number or not username:
            error1 = True
        elif len(number) < 9:
            error3 = True
        else:
            # 檢查是否存在相同工號
            existing_user = UserRegister.query.filter_by(number=number).first()
            if existing_user:
                error2 = True
            else:
                binary_data = base64.b64decode(capturedImageData.split(',')[1])

                # 轉face recognition encode
                image_pil = Image.open(io.BytesIO(binary_data))
                image_np = np.array(image_pil)
                img = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
                encode = face_recognition.face_encodings(img)[0]
                encode_data = pickle.dumps(encode)

                new_user = UserRegister(
                    number=number, username=username, signup_time=signup_time, captured_image=binary_data, encode_data=encode_data)
                db.session.add(new_user)
                db.session.commit()
    return render_template('register.html', error1=error1, error2=error2)
# --------------------------------------------------------------------------------------------#

# -----------------------------------------已註冊查看網頁---------------------------------------------#


@app.route('/view', methods=['GET'])
def view_users():
    users = UserRegister.query.all()  # 收集已註冊數據
    return render_template('view.html', users=users)
# --------------------------------------------------------------------------------------------#


@app.route('/delete/<number>', methods=['POST'])
def delete_user(number):
    user_to_delete = UserRegister.query.get(number)  # 根據工號查找要刪除的用戶
    if user_to_delete:
        db.session.delete(user_to_delete)  # 從資料庫中刪除用戶記錄
        db.session.commit()
    return redirect(url_for('view_users'))


peopleName = []  # 儲存姓名list
encodeListKnown = []  # 儲存encode
peopleID = []


@app.route('/')
def home():
    # Load the encoding file.

    print("Loading Started...")

    read_data = UserRegister.query.all()
    for user_data in read_data:
        retrieved_data = pickle.loads(user_data.encode_data)
        peopleName.append(user_data.username)
        encodeListKnown.append(retrieved_data)
        peopleID.append(user_data.number)
    print("Encode File Loaded")
    return render_template('home.html', peopleID=peopleID, peopleName=peopleName, encodeListKnown=encodeListKnown)


global n
global faceDis


def generate_frames():
    n = None
    camera0 = cv2.VideoCapture(0)

    while True:

        success, img = camera0.read()
        if not success:
            break

        if n == None:
            # 將image縮小並轉換成RGB
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            # 將臉轉換成encode
            faceCurFrame = face_recognition.face_locations(imgS)
            encodeCurFrame = face_recognition.face_encodings(
                imgS, faceCurFrame)
            # print(encodeCurFrame)
            # if encodeCurFrame.any():
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(
                    encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(
                    encodeListKnown, encodeFace)
                # print("matches", matches)
                # print("faceDis", faceDis)

            # # print("Match Index", matchIndex)
            # if faceDis:
                # Check if faceDis is not empty
                matchIndex = np.argmin(faceDis)
                if matches[matchIndex] and faceDis[matchIndex] <= 0.5:
                    print(peopleName[matchIndex])
                    n = peopleID[matchIndex]
                    # camera(n)
                    show(n)
                else:
                    print("Don't Known Face Detected")
            # else:
            #     print("No faces detected in the current frame")
        # else:
        #     print("No faces detected in the current frame")
        # 把获取到的图像格式转换(编码)成流数据，赋值到内存缓存中;
        # 主要用于图像数据格式的压缩，方便网络传输
        success, buffer = cv2.imencode('.jpg', img)
        # 将缓存里的流数据转成字节流
        frame = buffer.tobytes()
        # 指定字节流类型image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera0.release()
    cv2.destroyAllWindows()


# def get_dectecded_people(matchIndex):
#     id = peopleID[matchIndex]
#     name = peopleName[matchIndex]
#     return (id, name)


@app.route('/camera', methods=['GET'])
def camera():
    # user = None

    # if 'n' in request.args:
    #     n = request.args['n']
    # # user = None
    # # if n is not None:
    #     try:
    #         with app.app_context():
    #             # Query user with a specific number
    #             user = UserRegister.query.filter_by(number=n).first()
    #             # id = user.number
    #             # name = user.Username

    #     except Exception as ex:
    #         print(ex)
    #         # return render_template('error.html', message='An error occurred while searching for data.')
    # # else:
    # id = user.number if user else "none"
    # name = user.username if user else "none"
    # return render_template('camera.html', id=id, name=name)
    return render_template('camera.html')


@app.route('/show/<n>', methods=['GET'])
def show(n):
    with app.app_context():
        # try:
        #     with app.app_context():
        #         # Query user with a specific number
        #         user = UserRegister.query.filter_by(number=n).first()

        #     # You can now use the 'user' variable to access the queried data
        #         print(user)
        #         return render_template('camera.html', user=user)

        # except Exception as ex:
        #     print(ex)
        # return render_template('error.html', message='An error occurred while searching for data.')

        try:
            conn = pymysql.connect(**db_settings)
            with conn.cursor() as cursor:

                select_query = "SELECT number, username FROM topics.userregisters where number = %s "
                cursor.execute(select_query, n)
                result = cursor.fetchall()
                id = result[0][0]
                name = result[0][1]
                print(id)
            # 儲存變更
            conn.commit()
            # print("Multi-dimensional list successfully inserted into MySQL database")
            # 關閉連線
            conn.close()
            # response_data = {'status': 'success',
            #                  'id': result[0][0], 'name': result[0][1]}

            # Return JSON response
            # return {'status': 'success', 'id': id, 'name': name}
            return render_template('camera.html', result1=id, result2=name)
        except Exception as ex:  # 處理例外
            print(ex)
            # Return error response
            # return Response('status'= 'error', 'message': 'An error occurred')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)
