from flask import Flask, render_template, request, redirect, url_for, jsonify
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

# 取得啟動文件資料夾路徑
pjdir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# -------------資料庫設定---------------#
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:12345678@localhost/Topics'
# 隨機設定密碼
app.config['SECRET_KEY'] = secrets.token_hex(16)

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


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/camera')
def camera():
    return render_template('camera.html')


if __name__ == '__main__':
    app.run(debug=True)
