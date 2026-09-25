import os
import glob
from minio import Minio

# 1. Cấu hình kết nối MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "lakehouse-warehouse"
BRONZE_PREFIX = "bronze/tiki_books"

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# Đảm bảo bucket tồn tại
if not client.bucket_exists(BUCKET_NAME):
    client.make_bucket(BUCKET_NAME)
    print(f"✅ Đã tạo mới bucket: {BUCKET_NAME}")
else:
    print(f"ℹ️ Bucket '{BUCKET_NAME}' đã sẵn sàng.")

# 2. Quét tất cả file CSV trong thư mục data/raw_kaggle/
local_dir = os.path.join("data", "raw_kaggle")
csv_files = glob.glob(os.path.join(local_dir, "*.csv"))

if not csv_files:
    print(f"❌ Không tìm thấy file CSV nào trong thư mục '{local_dir}'! Hãy kiểm tra lại.")
    exit(1)

print(f"🚀 Bắt đầu tải {len(csv_files)} files lên s3://{BUCKET_NAME}/{BRONZE_PREFIX}/ ...\n")

for file_path in csv_files:
    file_name = os.path.basename(file_path)
    target_object_name = f"{BRONZE_PREFIX}/{file_name}"
    
    print(f"⏳ Đang tải: {file_name} -> {target_object_name}...")
    client.fput_object(
        bucket_name=BUCKET_NAME,
        object_name=target_object_name,
        file_path=file_path,
        content_type="text/csv"
    )

print(f"\n🎉 Hoàn thành! Toàn bộ file thô đã nằm an toàn tại s3://{BUCKET_NAME}/{BRONZE_PREFIX}/")