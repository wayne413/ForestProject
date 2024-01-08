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


# 读取图像
image_path = 'images1/Elon Musk.jpg'
image = cv2.imread(image_path)
if image is None:
    print(f"Error: Unable to read the image at path: {image_path}")
# 转换图像数据为字节流
image_bytes = cv2.imencode('.jpg', image)[1].tobytes()

# 连接到MySQL数据库
try:
    conn = pymysql.connect(**db_settings)
    with conn.cursor() as cursor:

        # 创建保存图像数据的表
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS images (id INT AUTO_INCREMENT PRIMARY KEY, image_data LONGBLOB)")

        # 将图像数据插入表中
        insert_query = "INSERT INTO images (img) VALUES (%s)"
        cursor.execute(insert_query, (image_bytes,))

        cursor.close()

    # 儲存變更
    conn.commit()

    # 關閉連線
    conn.close()

except Exception as e:
    print("错误:", e)
