import sqlite3
import json


class CanteenDB:
    def __init__(self, db_path="canteen_diet.db"):
        # 1. 建立数据库连接
        self.conn = sqlite3.connect(db_path)
        # 2. 初始化表结构
        self._create_tables()

    def _create_tables(self):
        # 执行 SQL 语句初始化表...
        sql_script = """
        CREATE TABLE IF NOT EXISTS canteens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canteen_name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS windows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canteen_id INTEGER,
            window_number TEXT NOT NULL,
            FOREIGN KEY (canteen_id) REFERENCES canteens(id)
        );

        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            window_id INTEGER,
            meal_type TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            feature_tags TEXT,
            description TEXT,
            FOREIGN KEY (window_id) REFERENCES windows(id)
        );

        CREATE TABLE IF NOT EXISTS dish_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER,
            ingredient_name TEXT NOT NULL,
            ingredient_type TEXT,
            FOREIGN KEY (dish_id) REFERENCES dishes(id)
        );

        CREATE TABLE IF NOT EXISTS dish_nutrition_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER,
            level_name TEXT NOT NULL,
            total_value REAL,
            ingredients TEXT,
            details TEXT,
            FOREIGN KEY (dish_id) REFERENCES dishes(id)
        );
        """
        try:
            self.conn.executescript(sql_script)
            self.conn.commit()
            print("食堂数据库表初始化成功")
        except Exception as e:
            print(f"初始化表失败: {e}")

    def save_canteen_data(self, canteen_data: dict):
        """
        保存食堂数据到数据库
        
        :param canteen_data: 食堂数据字典，格式如下：
            {
                "紫荆园": {
                    "1号窗口": {
                        "早餐": [
                            {
                                "dish_name": "豆浆",
                                "main_ingredients": ["黄豆"],
                                "seasonings": ["糖"],
                                "feature_tags": ["饮品", "早餐"],
                                "pagoda_nutrition_vector": {
                                    "L1": {...},
                                    "L2": {...},
                                    "L3": {...},
                                    "L4": {...},
                                    "L5": {"oil": 0, "salt": 0}
                                }
                            }
                        ],
                        "午餐/晚餐": [...]
                    }
                }
            }
        :return: 保存结果信息
        """
        cursor = self.conn.cursor()
        
        try:
            for canteen_name, windows in canteen_data.items():
                # 1. 插入或获取食堂ID
                cursor.execute("INSERT OR IGNORE INTO canteens (canteen_name) VALUES (?)", (canteen_name,))
                cursor.execute("SELECT id FROM canteens WHERE canteen_name = ?", (canteen_name,))
                canteen_id = cursor.fetchone()[0]
                
                for window_number, meals in windows.items():
                    # 2. 插入或获取窗口ID
                    cursor.execute('''
                        INSERT OR IGNORE INTO windows (canteen_id, window_number)
                        VALUES (?, ?)
                    ''', (canteen_id, window_number))
                    cursor.execute('''
                        SELECT id FROM windows 
                        WHERE canteen_id = ? AND window_number = ?
                    ''', (canteen_id, window_number))
                    window_id = cursor.fetchone()[0]
                    
                    for meal_type, dishes in meals.items():
                        # 3. 插入菜品信息
                        for dish in dishes:
                            cursor.execute('''
                                INSERT INTO dishes 
                                (window_id, meal_type, dish_name, feature_tags, description)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                window_id,
                                meal_type,
                                dish["dish_name"],
                                json.dumps(dish.get("feature_tags", []), ensure_ascii=False),
                                dish.get("description", "")
                            ))
                            dish_id = cursor.lastrowid
                            
                            # 4. 插入主要食材
                            main_ingredients = dish.get("main_ingredients", [])
                            for ingredient in main_ingredients:
                                cursor.execute('''
                                    INSERT INTO dish_ingredients 
                                    (dish_id, ingredient_name, ingredient_type)
                                    VALUES (?, ?, ?)
                                ''', (dish_id, ingredient, "main"))
                            
                            # 5. 插入调料
                            seasonings = dish.get("seasonings", [])
                            for seasoning in seasonings:
                                cursor.execute('''
                                    INSERT INTO dish_ingredients 
                                    (dish_id, ingredient_name, ingredient_type)
                                    VALUES (?, ?, ?)
                                ''', (dish_id, seasoning, "seasoning"))
                            
                            # 6. 插入营养等级数据
                            nutrition_vector = dish.get("pagoda_nutrition_vector", {})
                            for level_name, level_data in nutrition_vector.items():
                                if level_name == "L5":
                                    # L5 特殊处理：将 oil 和 salt 用逗号分隔存储
                                    oil = level_data.get("oil", 0)
                                    salt = level_data.get("salt", 0)
                                    total_value = f"{oil},{salt}"
                                    # L5 没有 ingredients 键，使用空数组
                                    ingredients_json = json.dumps([], ensure_ascii=False)
                                    details_json = json.dumps(level_data.get("details", {}), ensure_ascii=False)
                                else:
                                    # 其他等级：使用原有的 total_value
                                    total_value = level_data.get("total_value", 0)
                                    ingredients_json = json.dumps(level_data.get("ingredients", []), ensure_ascii=False)
                                    details_json = json.dumps(level_data.get("details", {}), ensure_ascii=False)
                                
                                cursor.execute('''
                                    INSERT INTO dish_nutrition_levels 
                                    (dish_id, level_name, total_value, ingredients, details)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (
                                    dish_id,
                                    level_name,
                                    total_value,
                                    ingredients_json,
                                    details_json
                                ))
            
            self.conn.commit()
            return "食堂数据保存成功"
            
        except Exception as e:
            self.conn.rollback()
            return f"保存失败: {e}"

    def get_canteen_list(self) -> list:
        """
        获取所有食堂列表
        
        :return: 食堂列表，每条记录包含 (id, canteen_name)
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, canteen_name FROM canteens")
        return cursor.fetchall()

    def get_windows_by_canteen(self, canteen_name: str) -> list:
        """
        获取指定食堂的所有窗口
        
        :param canteen_name: 食堂名称
        :return: 窗口列表，每条记录包含 (id, window_number)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT w.id, w.window_number
            FROM windows w
            JOIN canteens c ON w.canteen_id = c.id
            WHERE c.canteen_name = ?
        ''', (canteen_name,))
        return cursor.fetchall()

    def get_dishes_by_window(self, canteen_name: str, window_number: str, meal_type: str) -> list:
        """
        获取指定窗口的菜品列表
        
        :param canteen_name: 食堂名称
        :param window_number: 窗口号
        :param meal_type: 用餐类型（早餐、午餐/晚餐）
        :return: 菜品列表，每条记录包含 (id, dish_name, feature_tags)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT d.id, d.dish_name, d.feature_tags
            FROM dishes d
            JOIN windows w ON d.window_id = w.id
            JOIN canteens c ON w.canteen_id = c.id
            WHERE c.canteen_name = ? AND w.window_number = ? AND d.meal_type = ?
        ''', (canteen_name, window_number, meal_type))
        return cursor.fetchall()

    def get_dish_nutrition(self, dish_id: int) -> dict:
        """
        获取指定菜品的营养信息
        
        :param dish_id: 菜品ID
        :return: 营养信息字典，包含食材和营养等级
        """
        cursor = self.conn.cursor()
        
        # 获取食材信息
        cursor.execute('''
            SELECT ingredient_name, ingredient_type
            FROM dish_ingredients
            WHERE dish_id = ?
        ''', (dish_id,))
        ingredients = {}
        for row in cursor.fetchall():
            ingredient_type = row[1]
            if ingredient_type not in ingredients:
                ingredients[ingredient_type] = []
            ingredients[ingredient_type].append(row[0])
        
        # 获取营养等级信息
        cursor.execute('''
            SELECT level_name, total_value
            FROM dish_nutrition_levels
            WHERE dish_id = ?
        ''', (dish_id,))
        nutrition = {}
        for row in cursor.fetchall():
            level_name = row[0]
            total_value = row[1]
            
            if level_name == "L5":
                # L5 的 total_value 是 "oil,salt" 格式
                try:
                    parts = str(total_value).split(",")
                    if len(parts) == 2:
                        nutrition[level_name] = {
                            "oil": float(parts[0]),
                            "salt": float(parts[1])
                        }
                    else:
                        nutrition[level_name] = total_value
                except (ValueError, AttributeError):
                    nutrition[level_name] = total_value
            else:
                nutrition[level_name] = total_value
        
        return {
            "ingredients": ingredients,
            "nutrition": nutrition
        }

    def search_dishes_by_nutrition(self, nutrition_level: str, min_value: float = 0) -> list:
        """
        根据营养等级搜索菜品
        
        :param nutrition_level: 营养等级（L1, L2, L3, L4, L5）
        :param min_value: 最小值（对于 L5，可以传入 "oil" 或 "salt" 来搜索）
        :return: 匹配的菜品列表
        """
        cursor = self.conn.cursor()
        
        if nutrition_level == "L5":
            # L5 特殊处理：搜索油量或盐量
            cursor.execute('''
                SELECT d.id, d.dish_name, c.canteen_name, w.window_number, d.meal_type
                FROM dishes d
                JOIN windows w ON d.window_id = w.id
                JOIN canteens c ON w.canteen_id = c.id
                JOIN dish_nutrition_levels n ON d.id = n.dish_id
                WHERE n.level_name = 'L5'
            ''')
            results = []
            for row in cursor.fetchall():
                dish_id = row[0]
                nutrition_data = self.get_dish_nutrition(dish_id)
                oil_value = nutrition_data["nutrition"]["L5"]["oil"]
                salt_value = nutrition_data["nutrition"]["L5"]["salt"]
                
                if isinstance(min_value, str):
                    if min_value == "oil" and oil_value > 0:
                        results.append(row)
                    elif min_value == "salt" and salt_value > 0:
                        results.append(row)
                elif isinstance(min_value, (int, float)):
                    if oil_value >= min_value or salt_value >= min_value:
                        results.append(row)
            return results
        else:
            # 其他等级：搜索 total_value
            cursor.execute('''
                SELECT d.id, d.dish_name, c.canteen_name, w.window_number, d.meal_type
                FROM dishes d
                JOIN windows w ON d.window_id = w.id
                JOIN canteens c ON w.canteen_id = c.id
                JOIN dish_nutrition_levels n ON d.id = n.dish_id
                WHERE n.level_name = ? AND n.total_value >= ?
            ''', (nutrition_level, min_value))
            return cursor.fetchall()


if __name__ == "__main__":
    # 使用示例
    db_path = "/data3/yjy/envs/agent/agent_codes/Nutrition_agent/database/canteen_diet.db"
    db = CanteenDB(db_path)


    with open("Nutrition_agent/dish_data/canteen_menu_data.json", "r", encoding="utf-8") as f:
        canteen_data = json.load(f)

    # 保存食堂数据
    result = db.save_canteen_data(canteen_data)
    print(result)