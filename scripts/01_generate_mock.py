import json
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

categories = ["Laptop", "Smartphone", "Tai nghe", "Màn hình", "Bàn phím cơ"]
brands = ["Apple", "Dell", "Asus", "Logitech", "Samsung", "Sony"]

def generate_mock_data(num_products=40, num_days=7):
    base_date = datetime.now() - timedelta(days=num_days)
    
    # 1. Danh mục sản phẩm cố định
    catalog = []
    for i in range(1, num_products + 1):
        catalog.append({
            "product_id": f"PROD_{i:04d}",
            "sku": f"SKU-{random.randint(10000, 99999)}",
            "name": f"{random.choice(brands)} {fake.word().title()} {random.choice(categories)}",
            "brand": random.choice(brands),
            "category_name": random.choice(categories),
            "base_price": round(random.uniform(1_000_000, 30_000_000), -4)
        })

    # 2. Biến động giá qua từng ngày
    records = []
    for day_offset in range(num_days):
        current_day = base_date + timedelta(days=day_offset)
        crawled_date = current_day.strftime("%Y-%m-%d")
        crawled_at = current_day.strftime("%Y-%m-%d %H:%M:%S")

        for item in catalog:
            discount_rate = random.choice([0.05, 0.1, 0.15, 0.2]) if random.random() < 0.25 else 0.0
            price = item["base_price"] * (1 - discount_rate)

            records.append({
                "product_id": item["product_id"],
                "sku": item["sku"],
                "name": item["name"],
                "brand": item["brand"],
                "category_name": item["category_name"],
                "price": float(price),
                "market_price": float(item["base_price"]),
                "discount_rate": float(discount_rate),
                "rating_score": round(random.uniform(3.5, 5.0), 1),
                "review_count": random.randint(10, 800),
                "crawled_date": crawled_date,
                "crawled_at": crawled_at
            })

    return records

if __name__ == "__main__":
    records = generate_mock_data()
    output_path = "data/mock_bronze_tiki.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã tạo thành công {len(records)} dòng dữ liệu vào {output_path}")