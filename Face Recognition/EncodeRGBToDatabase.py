import cv2
import face_recognition
import os
import pymysql
import numpy as np
import pickle

# 資料庫參數設定
db_settings = {
    "host": "localhost",
    "port": 3306,
    "user": "test",
    "password": "12345678",
    "db": "topics",
    "charset": "utf8",
}

# 讀取資料夾內的檔案
folderPath = 'images1'
pathList = os.listdir(folderPath)

imgList = []
peopleName = []
binaryList = []

for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    peopleName.append(os.path.splitext(path)[0])

# 將轉換的encode轉成二進制


def fingEncodings(imagesList):
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        # print(encode)
        binary_data = pickle.dumps(encode)
        binaryList.append(binary_data)
    return binaryList


print("Encoding Started...")
encodeListKnown = fingEncodings(imgList)
encodeListKnownWithNames = [peopleName, binaryList]
print("Encoding Complete")

# 將name、encode寫入資料庫
try:
    conn = pymysql.connect(**db_settings)
    with conn.cursor() as cursor:
        arr1 = ["name", "encode"]
        command = "INSERT INTO people(name,encode)VALUES(%s,%s)"
        dictionary = {i: j for i, j in zip(arr1, encodeListKnownWithNames)}
        cursor.execute(
            command, (dictionary["name"], dictionary["encode"]))

    # 儲存變更
    conn.commit()
    # print("Multi-dimensional list successfully inserted into MySQL database")
    # 關閉連線
    conn.close()

except Exception as ex:  # 處理例外
    print(ex)

# 將資料庫內的encode讀取出來
# try:
#     conn = pymysql.connect(**db_settings)
#     with conn.cursor() as cursor:

#         select_query = "SELECT encode FROM people WHERE name = 'ElonMusk'"
#         cursor.execute(select_query)
#         result = cursor.fetchone()
#         if result:
#             # 将二进制数据反序列化为多维列表
#             retrieved_data = pickle.loads(result[0])

#             # 打印结果
#             print("从 MySQL 中讀取的多维列表:", retrieved_data)

#     # 儲存變更
#     conn.commit()
#     print("Multi-dimensional list successfully inserted into MySQL database")
#     # 關閉連線
#     conn.close()

# except Exception as ex:  # 處理例外
#     print(ex)
