import cv2
import pickle
import face_recognition
import numpy as np
import cvzone
import pymysql

peopleName = []  # 儲存姓名list
encodeListKnown = []  # 儲存encode

# 資料庫參數設定
db_settings = {
    "host": "localhost",
    "port": 3306,
    "user": "test",
    "password": "12345678",
    "db": "topics",
    "charset": "utf8",
}

# 使用筆電鏡頭
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# 背景
imgbackground = cv2.imread("resources/background.png")

# Load the encoding file
print("Loading Started...")

# 將資料庫內的name、encode讀取出來
try:
    conn = pymysql.connect(**db_settings)
    with conn.cursor() as cursor:

        select_query = "SELECT * FROM people "
        cursor.execute(select_query)
        result = cursor.fetchall()
        for i in range(len(result)):
            retrieved_data = pickle.loads(result[i][1])
            peopleName.append(result[i][0])
            encodeListKnown.append(retrieved_data)

    # 儲存變更
    conn.commit()
    # print("Multi-dimensional list successfully inserted into MySQL database")
    # 關閉連線
    conn.close()

except Exception as ex:  # 處理例外
    print(ex)

print("Encode File Loaded")

while True:
    success, img = cap.read()
    # 將image縮小並轉換成RGB
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    # 將臉轉換成encode
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    # 將攝影機的影像覆蓋在底圖上 [230~810,55~695]
    imgbackground[230:230+480, 55:55+640] = img

    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        # print("matches", matches)
        # print("faceDis", faceDis)

        # 加入人臉的偵測框線
        matchIndex = np.argmin(faceDis)
        # print("Match Index", matchIndex)
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
        bbox = 55+x1, 230+y1, x2-x1, y2-y1
        cvzone.cornerRect(imgbackground, bbox, rt=0)

        # 判斷人臉身分
        if matches[matchIndex] & (faceDis[matchIndex] <= 0.5):
            # print("Known Face Detected")
            print(peopleName[matchIndex])
        else:
            print("Don't Known Face Detected")
    cv2.imshow("Camera", img)
    cv2.imshow("Face Arrendance", imgbackground)

    # cv2.waitKey(1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
