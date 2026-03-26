"""
模擬餐廳資料庫 — 工作坊共用種子資料
"""

RESTAURANT_DB = [
    # === 日式料理 ===
    {
        "name": "築地鮮魚",
        "cuisine": "japanese",
        "budget_level": "budget",
        "avg_price": 200,
        "rating": 4.2,
        "location": "台北市大安區",
        "specialty": "平價生魚片丼飯",
    },
    {
        "name": "鶴橋拉麵",
        "cuisine": "japanese",
        "budget_level": "budget",
        "avg_price": 180,
        "rating": 4.0,
        "location": "台北市中山區",
        "specialty": "豚骨拉麵",
    },
    {
        "name": "隱家日式料理",
        "cuisine": "japanese",
        "budget_level": "premium",
        "avg_price": 800,
        "rating": 4.7,
        "location": "台北市信義區",
        "specialty": "無菜單料理",
    },
    {
        "name": "松濤割烹",
        "cuisine": "japanese",
        "budget_level": "premium",
        "avg_price": 1200,
        "rating": 4.9,
        "location": "台北市大安區",
        "specialty": "懷石料理",
    },
    # === 義式料理 ===
    {
        "name": "巷弄披薩屋",
        "cuisine": "italian",
        "budget_level": "budget",
        "avg_price": 250,
        "rating": 4.1,
        "location": "台北市松山區",
        "specialty": "手工窯烤披薩",
    },
    {
        "name": "小義大利廚房",
        "cuisine": "italian",
        "budget_level": "budget",
        "avg_price": 280,
        "rating": 4.3,
        "location": "台北市中正區",
        "specialty": "義大利麵與燉飯",
    },
    {
        "name": "Trattoria Bella",
        "cuisine": "italian",
        "budget_level": "premium",
        "avg_price": 900,
        "rating": 4.6,
        "location": "台北市大安區",
        "specialty": "手工義大利麵配松露",
    },
    {
        "name": "La Dolce Vita",
        "cuisine": "italian",
        "budget_level": "premium",
        "avg_price": 1500,
        "rating": 4.8,
        "location": "台北市信義區",
        "specialty": "義式Fine Dining",
    },
    # === 台式料理 ===
    {
        "name": "阿嬤的灶腳",
        "cuisine": "taiwanese",
        "budget_level": "budget",
        "avg_price": 120,
        "rating": 4.4,
        "location": "台北市萬華區",
        "specialty": "古早味滷肉飯",
    },
    {
        "name": "好記擔仔麵",
        "cuisine": "taiwanese",
        "budget_level": "budget",
        "avg_price": 150,
        "rating": 4.2,
        "location": "台北市中山區",
        "specialty": "擔仔麵與小菜",
    },
    {
        "name": "山海樓",
        "cuisine": "taiwanese",
        "budget_level": "premium",
        "avg_price": 1000,
        "rating": 4.8,
        "location": "台北市中山區",
        "specialty": "精緻台菜",
    },
    # === 韓式料理 ===
    {
        "name": "首爾之家",
        "cuisine": "korean",
        "budget_level": "budget",
        "avg_price": 220,
        "rating": 4.0,
        "location": "台北市中山區",
        "specialty": "韓式炸雞與部隊鍋",
    },
    {
        "name": "韓國烤肉王",
        "cuisine": "korean",
        "budget_level": "premium",
        "avg_price": 700,
        "rating": 4.5,
        "location": "台北市大安區",
        "specialty": "頂級韓牛燒烤",
    },
    # === 泰式料理 ===
    {
        "name": "曼谷街頭",
        "cuisine": "thai",
        "budget_level": "budget",
        "avg_price": 200,
        "rating": 4.1,
        "location": "台北市公館區",
        "specialty": "平價打拋豬肉飯",
    },
    {
        "name": "清邁小廚",
        "cuisine": "thai",
        "budget_level": "budget",
        "avg_price": 250,
        "rating": 4.3,
        "location": "台北市大安區",
        "specialty": "海鮮冬蔭功湯",
    },
    {
        "name": "暹羅皇朝",
        "cuisine": "thai",
        "budget_level": "premium",
        "avg_price": 850,
        "rating": 4.7,
        "location": "台北市信義區",
        "specialty": "精緻泰式咖哩與海鮮",
    },
]


def search_restaurants(
    cuisine: str | None = None,
    budget_level: str | None = None,
    max_price: int | None = None,
) -> list[dict]:
    """
    搜尋餐廳。

    Args:
        cuisine: 料理類型 ("japanese", "italian", "taiwanese", "korean")
        budget_level: 預算等級 ("budget" or "premium")
        max_price: 最高價格

    Returns:
        符合條件的餐廳列表，依評分排序
    """
    results = RESTAURANT_DB

    if cuisine:
        results = [r for r in results if r["cuisine"] == cuisine.lower()]

    if budget_level:
        results = [r for r in results if r["budget_level"] == budget_level.lower()]

    if max_price:
        results = [r for r in results if r["avg_price"] <= max_price]

    results.sort(key=lambda r: r["rating"], reverse=True)

    return results
