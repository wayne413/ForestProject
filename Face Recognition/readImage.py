import pymysql
import io
from PIL import Image

# 資料庫連線
db_settings = {
    "host": "localhost",
    "port": 3306,
    "user": "test",
    "password": "12345678",
    "db": "topics",
    "charset": "utf8",
}

# 讀取image
try:
    conn = pymysql.connect(**db_settings)
    with conn.cursor() as cursor:
        cursor = conn.cursor()

        # 從資料庫取得影像
        # 指定id為1的影像
        cursor.execute("SELECT img FROM image WHERE id = 1")
        result = cursor.fetchone()

        if result:
            # 將二進制轉換成圖片
            image_data = result[0]
            image = Image.open(io.BytesIO(image_data))

            # 顯示圖片
            image.show()

        # 儲存變更
        conn.commit()

        # 關閉連線
        conn.close()

except Exception as ex:  # 處理例外
    print(ex)
