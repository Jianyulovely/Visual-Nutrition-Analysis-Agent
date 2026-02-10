import sqlite3
import json



class UserDB:
    def __init__(self, db_path="user_diet.db"):
        # 1. 建立数据库连接
        self.conn = sqlite3.connect(db_path)
        # 2. 初始化表结构
        self._create_tables()

    def _create_tables(self):
        # 执行 SQL 语句初始化表...
        sql_script = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_menu_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dish_name TEXT NOT NULL,
            feature_tags TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS menu_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER,
            ingredient_name TEXT NOT NULL,
            ingredient_type TEXT,
            FOREIGN KEY (menu_id) REFERENCES user_menu_history(id)
        );

        CREATE TABLE IF NOT EXISTS menu_nutrition_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER,
            level_name TEXT NOT NULL,
            total_value REAL,
            ingredients TEXT,
            details TEXT,
            FOREIGN KEY (menu_id) REFERENCES user_menu_history(id)
        );
        """
        try:
            self.conn.executescript(sql_script)
            self.conn.commit()
            print("数据库表初始化成功")
        except Exception as e:
            print(f"初始化表失败: {e}")

    def save_analysis_report(self, username: str, report_json: dict):
        """
        将分析报告存入数据库
        """
        cursor = self.conn.cursor()
        
        # 1. 获取或创建用户 ID
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]

        #2. 插入菜单基本信息
        cursor.execute('''
            INSERT INTO user_menu_history 
            (user_id, dish_name, feature_tags, description) 
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            report_json["dish_name"],
            json.dumps(report_json["feature_tags"], ensure_ascii=False),
            report_json.get("description", "")
        ))
        menu_id = cursor.lastrowid

        # 3. 插入主要食材
        main_ingredients = report_json.get("main_ingredients", [])
        for ingredient in main_ingredients:
            cursor.execute('''
                INSERT INTO menu_ingredients (menu_id, ingredient_name, ingredient_type)
                VALUES (?, ?, ?)
            ''', (menu_id, ingredient, "main"))

        # 4. 插入调料
        seasonings = report_json.get("seasonings", [])
        for seasoning in seasonings:
            cursor.execute('''
                INSERT INTO menu_ingredients (menu_id, ingredient_name, ingredient_type)
                VALUES (?, ?, ?)
            ''', (menu_id, seasoning, "seasoning"))

        # 5. 插入营养等级数据
        nutrition_vector = report_json.get("pagoda_nutrition_vector", {})
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
                INSERT INTO menu_nutrition_levels 
                (menu_id, level_name, total_value, ingredients, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                menu_id,
                level_name,
                total_value,
                ingredients_json,
                details_json
            ))
        
        self.conn.commit()
        return f"已成功记录 {username} 的历史菜单：{report_json['dish_name']}"

    def get_menu_ingredients_count(self, menu_id: int) -> dict:
        """
        获取指定菜单的食材数量统计
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT ingredient_type, COUNT(*) as count
            FROM menu_ingredients
            WHERE menu_id = ?
            GROUP BY ingredient_type
        ''', (menu_id,))
        
        result = {}
        for row in cursor.fetchall():
            result[row[0]] = row[1]
        
        return result

    def get_menu_nutrition_summary(self, menu_id: int) -> dict:
        """
        获取指定菜单的营养等级汇总（重点是 total_value）
        对于 L5 等级，total_value 是逗号分隔的 "oil,salt" 格式
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT level_name, total_value
            FROM menu_nutrition_levels
            WHERE menu_id = ?
        ''', (menu_id,))
        
        result = {}
        for row in cursor.fetchall():
            level_name = row[0]
            total_value = row[1]
            
            if level_name == "L5":
                # L5 的 total_value 是 "oil,salt" 格式
                try:
                    parts = str(total_value).split(",")
                    if len(parts) == 2:
                        result[level_name] = {
                            "oil": float(parts[0]),
                            "salt": float(parts[1])
                        }
                    else:
                        result[level_name] = total_value
                except (ValueError, AttributeError):
                    result[level_name] = total_value
            else:
                result[level_name] = total_value
        
        return result

    def get_user_menu_history(self, username: str, k: int = None) -> list:
        """
        获取用户的菜单历史
        
        :param username: 用户名
        :param k: 要获取的最后 k 条记录，如果为 None 则获取所有记录
        :return: 菜单历史列表，每条记录包含 (id, dish_name, created_at)
        """
        cursor = self.conn.cursor()
        
        if k is None:
            cursor.execute('''
                SELECT h.id, h.dish_name, h.created_at
                FROM user_menu_history h
                JOIN users u ON h.user_id = u.user_id
                WHERE u.username = ?
                ORDER BY h.created_at DESC
            ''', (username,))
        else:
            cursor.execute('''
                SELECT h.id, h.dish_name, h.created_at
                FROM user_menu_history h
                JOIN users u ON h.user_id = u.user_id
                WHERE u.username = ?
                ORDER BY h.created_at DESC
                LIMIT ?
            ''', (username, k))
        
        return cursor.fetchall()

    def del_user_menu_history(self, username: str) -> str:
        """
        清除指定用户的所有历史菜单数据
        
        :param username: 用户名
        :return: 操作结果信息
        """
        cursor = self.conn.cursor()
        
        try:
            # 1. 获取用户ID
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if not result:
                return f"用户 {username} 不存在"
            
            user_id = result[0]
            
            # 2. 获取该用户的所有菜单ID
            cursor.execute("SELECT id FROM user_menu_history WHERE user_id = ?", (user_id,))
            menu_ids = [row[0] for row in cursor.fetchall()]
            
            if not menu_ids:
                return f"用户 {username} 没有历史菜单数据"
            
            # 3. 删除关联的食材记录
            placeholders = ','.join(['?' for _ in menu_ids])
            cursor.execute(f'''
                DELETE FROM menu_ingredients
                WHERE menu_id IN ({placeholders})
            ''', menu_ids)
            
            # 4. 删除关联的营养等级记录
            cursor.execute(f'''
                DELETE FROM menu_nutrition_levels
                WHERE menu_id IN ({placeholders})
            ''', menu_ids)
            
            # 5. 删除菜单历史记录
            cursor.execute("DELETE FROM user_menu_history WHERE user_id = ?", (user_id,))
            
            # 6. 删除用户记录
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            self.conn.commit()
            return f"已成功清除用户 {username} 的所有历史菜单数据"
            
        except Exception as e:
            self.conn.rollback()
            return f"清除失败: {e}"

    def clr_db(self) -> str:
        """
        清空数据库所有数据（保留表结构）
        
        :return: 操作结果信息
        """
        cursor = self.conn.cursor()
        
        try:
            # 1. 清空所有表的数据（按照外键依赖顺序）
            cursor.execute("DELETE FROM menu_nutrition_levels")
            cursor.execute("DELETE FROM menu_ingredients")
            cursor.execute("DELETE FROM user_menu_history")
            cursor.execute("DELETE FROM users")
            
            # 2. 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='user_menu_history'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu_ingredients'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='menu_nutrition_levels'")
            
            self.conn.commit()
            return "数据库已成功清空"
            
        except Exception as e:
            self.conn.rollback()
            return f"清空数据库失败: {e}"

    def get_nutrition_c_vector(self, username: str, meal_time: str) -> list:
        """
        获取用户指定时间段的营养六维向量
        
        :param username: 用户名
        :param meal_time: 用餐时间（breakfast, lunch, dinner）
        :return: 六维营养向量 [L1, L2, L3, L4, L5.oil, L5.salt]
        """
        cursor = self.conn.cursor()
        
        # 1. 获取用户当日的所有用餐记录
        cursor.execute('''
            SELECT h.id, h.dish_name, h.created_at
            FROM user_menu_history h
            JOIN users u ON h.user_id = u.user_id
            WHERE u.username = ? AND DATE(h.created_at) = DATE('now', 'localtime')
            ORDER BY h.created_at DESC
        ''', (username,))
        
        menu_records = cursor.fetchall()
        
        if not menu_records:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        # 2. 根据时间区间划分用餐记录
        from datetime import datetime, timedelta
        
        # 定义时间区间
        breakfast_start = datetime.strptime("05:00", "%H:%M").time()
        breakfast_end = datetime.strptime("10:00", "%H:%M").time()
        lunch_start = datetime.strptime("10:00", "%H:%M").time()
        lunch_end = datetime.strptime("15:00", "%H:%M").time()
        
        # 分类用餐记录
        breakfast_menus = []
        lunch_menus = []
        dinner_menus = []
        
        for menu_id, dish_name, created_at in menu_records:
            # created_at 是一个字符串，使用 strptime 转换为 datetime 对象
            if isinstance(created_at, str):
                 created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                 
            # 转换为东八区时间
            created_at = created_at + timedelta(hours=8)
            menu_time = created_at.time()
            
            if breakfast_start <= menu_time < breakfast_end:
                breakfast_menus.append(menu_id)
            elif lunch_start <= menu_time < lunch_end:
                lunch_menus.append(menu_id)
            else:
                dinner_menus.append(menu_id)
        
        # 3. 根据meal_time获取对应的菜单ID列表
        if meal_time == "breakfast":
            target_menus = breakfast_menus
        elif meal_time == "lunch":
            target_menus = lunch_menus
        elif meal_time == "dinner":
            target_menus = dinner_menus
        else:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        if not target_menus:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        # 4. 获取所有目标菜单的营养数据
        placeholders = ','.join(['?' for _ in target_menus])
        cursor.execute(f'''
            SELECT n.level_name, n.total_value
            FROM menu_nutrition_levels n
            WHERE n.menu_id IN ({placeholders})
        ''', target_menus)
        
        nutrition_data = cursor.fetchall()
        
        # 5. 提取L1-L5的total_value，L5特殊处理oil和salt
        result = {
            "L1": 0.0,
            "L2": 0.0,
            "L3": 0.0,
            "L4": 0.0,
            "L5": {"oil": 0.0, "salt": 0.0}
        }
        
        for level_name, total_value in nutrition_data:
            if level_name == "L5":
                # L5 特殊处理：将 oil 和 salt 分离
                try:
                    parts = str(total_value).split(",")
                    if len(parts) == 2:
                        result["L5"] = {
                            "oil": float(parts[0]),
                            "salt": float(parts[1])
                        }
                    else:
                        result["L5"] = total_value
                except (ValueError, AttributeError):
                    result["L5"] = total_value
            else:
                # 其他等级：直接使用 total_value
                result[level_name] = total_value
        
        # 6. 返回六维向量 [L1, L2, L3, L4, L5.oil, L5.salt]
        return [
            float(result["L1"]),
            float(result["L2"]),
            float(result["L3"]),
            float(result["L4"]),
            float(result["L5"]["oil"]),
            float(result["L5"]["salt"])
        ]


if __name__ == "__main__":
    # 使用示例
    user_db_path = "/data3/yjy/envs/agent/agent_codes/Nutrition_agent/database/user_diet.db"
    db = UserDB(user_db_path)

    report_data = {
        "dish_name": "西红柿炒鸡蛋",
        "main_ingredients": ["西红柿", "鸡蛋"],
        "seasonings": ["盐", "味精"],
        "pagoda_nutrition_vector": {
            "L1": { "total_value": 0, "ingredients": [], "details": { "grains": 0, "tubers": 0 } }, 
            "L2": { "total_value": 200, "ingredients": ["西红柿"], "details": { "vegetables": 200, "fruits": 0 } },
            "L3": { "total_value": 100, "ingredients": ["鸡蛋"], "details": { "animal_meat": 0, "seafood": 0, "eggs": 100 } },
            "L4": { "total_value": 0, "ingredients": [], "details": { "dairy": 0, "soy_nuts": 0 } },
            "L5": { "ingredients": [], "oil": 15.5, "salt": 3.2 }
        },
        "feature_tags": ["家常味", "快炒"],
        "description": "10字以内描述"
    }
    
    result = db.save_analysis_report("张三", report_data)
    print(result)
    
    # 演示查询功能
    print("\n" + "="*50)
    print("查询演示")
    print("="*50)
    
    # 1. 获取用户所有菜单历史
    all_history = db.get_user_menu_history("张三")
    print(f"\n用户所有菜单历史：{all_history}")
    
    # 2. 获取用户最后 1 个菜单
    last_1_menu = db.get_user_menu_history("张三", k=1)
    print(f"\n用户最后 1 个菜单：{last_1_menu}")
    
    # 3. 获取用户最后 3 个菜单
    last_3_menus = db.get_user_menu_history("张三", k=3)
    print(f"\n用户最后 3 个菜单：{last_3_menus}")
    
    if all_history:
        menu_id = all_history[0][0]
        
        # 4. 获取食材数量统计
        ingredients_count = db.get_menu_ingredients_count(menu_id)
        print(f"\n食材数量统计：{ingredients_count}")
        
        # 5. 获取营养等级汇总（重点：total_value）
        nutrition_summary = db.get_menu_nutrition_summary(menu_id)
        print(f"\n营养等级汇总（total_value）：{nutrition_summary}")
    
    # 演示删除功能
    print("\n" + "="*50)
    print("删除功能演示")
    print("="*50)
    
    # 1. 清除用户历史菜单
    del_result = db.del_user_menu_history("张三")
    print(f"\n{del_result}")
    
    # 2. 清空数据库
    # clr_result = db.clr_db()
    # print(f"\n{clr_result}")
