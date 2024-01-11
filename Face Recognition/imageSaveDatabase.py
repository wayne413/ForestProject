import numpy as np
import cv2
import face_recognition
import os
import pymysql
import hashlib

# 資料庫參數設定
db_settings = {
    "host": "localhost",
    "port": 3306,
    "user": "test",
    "password": "12345678",
    "db": "topics",
    "charset": "utf8",
}


# 讀取image
image_path = 'images1/Elon Musk.jpg'
image = cv2.imread(image_path)
if image is None:
    print(f"Error: Unable to read the image at path: {image_path}")
# 將image轉成bytes
image_bytes = cv2.imencode('.jpg', image)[1].tobytes()

# 寫入資料庫
try:
    conn = pymysql.connect(**db_settings)
    with conn.cursor() as cursor:

        insert_query = "INSERT INTO images (img) VALUES (%s)"
        cursor.execute(insert_query, (image_bytes,))

        cursor.close()

    # 儲存變更
    conn.commit()

    # 關閉連線
    conn.close()

except Exception as e:
    print("错误:", e)
