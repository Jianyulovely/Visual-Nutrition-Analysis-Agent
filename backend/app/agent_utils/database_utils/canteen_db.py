import chromadb
import json
import uuid
import sys
import os

# 添加父目录到 sys.path，以便导入 get_embed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from get_embed import DashScopeEmbeddingAdapter


class CanteenDB:
    def __init__(self, db_path="/data3/yjy/envs/agent/agent_codes/Nutrition_agent/database/canteen_chroma"):
        
        # 初始化客户端与千问 Embedding
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = DashScopeEmbeddingAdapter()
        
        # 获取或创建集合（菜品库）
        self.collection = self.client.get_or_create_collection(
            name="canteen_dishes",
            embedding_function=self.embedding_fn
        )

    def save_canteen_data(self, canteen_data: dict):
        """
        保存食堂数据到 Chroma
        """
        ids, metadatas, documents = [], [], []

        for canteen_name, windows in canteen_data.items():
            for window_number, meals in windows.items():
                for meal_type, dishes in meals.items():
                    for dish in dishes:
                        record_id = str(uuid.uuid4())
                        
                        # 提取核心营养数值用于后续 SQL 样式的范围筛选 ($gte, $lte)
                        vector = dish.get("pagoda_nutrition_vector", {})
                        
                        # 扁平化元数据：Chroma metadata 不支持嵌套，需将数值直接提取出来
                        metadata = {
                            "record_id": record_id,
                            "canteen_name": canteen_name,
                            "window_number": window_number,
                            "meal_type": meal_type,
                            "dish_name": dish["dish_name"],
                            "feature_tags": json.dumps(dish.get("feature_tags", []), ensure_ascii=False),
                            "description": dish.get("description", ""),
                            "main_ingredients": json.dumps(dish.get("main_ingredients", []), ensure_ascii=False),
                            "seasonings": json.dumps(dish.get("seasonings", []), ensure_ascii=False),
                            "L1": float(vector.get("L1", {}).get("total_value", 0)),
                            "L2": float(vector.get("L2", {}).get("total_value", 0)),
                            "L3": float(vector.get("L3", {}).get("total_value", 0)),
                            "L4": float(vector.get("L4", {}).get("total_value", 0)),
                            "L5_oil": float(vector.get("L5", {}).get("oil", 0)),
                            "L5_salt": float(vector.get("L5", {}).get("salt", 0)),
                            "full_nutrition_json": json.dumps(vector, ensure_ascii=False)
                        }
                        
                        ids.append(record_id)
                        metadatas.append(metadata)
                        # 将菜品名称、特征标签、以及菜品描述作为 Document 内容，用于语义搜索
                        documents.append(f"{dish.get('dish_name')} {dish.get('feature_tags', '')} {dish.get('description', '')}")

        if ids:
            self.collection.add(ids=ids, metadatas=metadatas, documents=documents)
        return f"已成功保存 {len(ids)} 个菜品到本地向量库"

    def get_canteen_list(self) -> list:
        """获取所有食堂列表"""
        results = self.collection.get()
        return list(set([m["canteen_name"] for m in results["metadatas"]]))

    def get_windows_by_canteen(self, canteen_name: str) -> list:
        """
        获取指定食堂的所有窗口
        
        :param canteen_name: 食堂名称
        :return: 窗口列表
        """
        results = self.collection.get(
            where={"canteen_name": canteen_name}
        )
        
        windows = set()
        for meta in results["metadatas"]:
            windows.add(meta["window_number"])
        
        return sorted(list(windows))

    def get_dishes_by_window(self, canteen_name: str, window_number: str, meal_type: str) -> list:
        """精确筛选：根据食堂、窗口和餐时获取菜品"""
        results = self.collection.get(
            where={
                "$and": [
                    {"canteen_name": canteen_name},
                    {"window_number": window_number},
                    {"meal_type": meal_type}
                ]
            }
        )
        
        dishes = []
        for meta in results["metadatas"]:
            dishes.append({
                "record_id": meta.get("record_id"),
                "dish_name": meta["dish_name"],
                "feature_tags": json.loads(meta.get("feature_tags", "[]")),
                "description": meta.get("description", "")
            })
        
        return dishes

    def get_dish_nutrition(self, dish_id: str) -> dict:
        """
        获取指定菜品的营养信息
        
        :param dish_id: 菜品ID（record_id）
        :return: 营养信息字典，包含食材和营养等级
        """
        results = self.collection.get(
            ids=[dish_id]
        )
        
        if not results["metadatas"]:
            return {}
        
        meta = results["metadatas"][0]
        
        # 解析食材信息
        ingredients = {}
        if meta.get("main_ingredients"):
            ingredients["main"] = json.loads(meta["main_ingredients"])
        if meta.get("seasonings"):
            ingredients["seasoning"] = json.loads(meta["seasonings"])
        
        # 解析营养等级信息
        nutrition = {}
        nutrition["L1"] = meta.get("L1", 0)
        nutrition["L2"] = meta.get("L2", 0)
        nutrition["L3"] = meta.get("L3", 0)
        nutrition["L4"] = meta.get("L4", 0)
        nutrition["L5"] = {
            "oil": meta.get("L5_oil", 0),
            "salt": meta.get("L5_salt", 0)
        }
        
        return {
            "ingredients": ingredients,
            "nutrition": nutrition
        }

    def search_dishes_by_nutrition(self, nutrition_level: str, min_value: float = 0) -> list:
        """
        根据营养等级搜索菜品
        
        :param nutrition_level: 营养等级（L1, L2, L3, L4, L5）
        :param min_value: 最小值（对于 L5，可以传入 oil 或 salt）
        :return: 匹配的菜品列表
        """
        results = self.collection.get()
        
        matched_dishes = []
        
        for meta in results["metadatas"]:
            if nutrition_level == "L5":
                # L5 特殊处理：搜索油量或盐量
                if isinstance(min_value, str):
                    if min_value == "oil" and meta.get("L5_oil", 0) >= min_value:
                        matched_dishes.append(meta)
                    elif min_value == "salt" and meta.get("L5_salt", 0) >= min_value:
                        matched_dishes.append(meta)
                elif isinstance(min_value, (int, float)):
                    if meta.get("L5_oil", 0) >= min_value or meta.get("L5_salt", 0) >= min_value:
                        matched_dishes.append(meta)
            else:
                # 其他等级：直接比较
                field_name = nutrition_level
                if meta.get(field_name, 0) >= min_value:
                    matched_dishes.append(meta)
        
        return matched_dishes

    def search_dishes_by_nutrition_range(self, nutrition_level: str, min_value: float, max_value: float) -> list:
        """
        根据营养等级范围搜索菜品
        
        :param nutrition_level: 营养等级（L1, L2, L3, L4）
        :param min_value: 最小值
        :param max_value: 最大值
        :return: 匹配的菜品列表
        """
        results = self.collection.get()
        
        matched_dishes = []
        
        for meta in results["metadatas"]:
            field_name = nutrition_level
            value = meta.get(field_name, 0)
            if min_value <= value <= max_value:
                matched_dishes.append(meta)
        
        return matched_dishes

    def search_dishes_by_L5(self, min_oil: float = None, max_oil: float = None, 
                            min_salt: float = None, max_salt: float = None) -> list:
        """
        根据 L5 营养（油和盐）的范围搜索菜品
        
        :param min_oil: 最小油量
        :param max_oil: 最大油量
        :param min_salt: 最小盐量
        :param max_salt: 最大盐量
        :return: 匹配的菜品列表
        """
        results = self.collection.get()
        
        matched_dishes = []
        
        for meta in results["metadatas"]:
            oil = meta.get("L5_oil", 0)
            salt = meta.get("L5_salt", 0)
            
            oil_match = True
            salt_match = True
            
            if min_oil is not None and oil < min_oil:
                oil_match = False
            if max_oil is not None and oil > max_oil:
                oil_match = False
            if min_salt is not None and salt < min_salt:
                salt_match = False
            if max_salt is not None and salt > max_salt:
                salt_match = False
            
            if oil_match and salt_match:
                matched_dishes.append(meta)
        
        return matched_dishes

    def semantic_search_dishes(self, query: str, n_results: int = 3):
        """
        核心优势：语义搜索
        例如输入"我想吃清淡点的"，Chroma 会自动调用千问向量进行匹配
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results["metadatas"] or not results["metadatas"][0]:
            return []
        
        return results["metadatas"][0]

    def get_dishes_by_filter(self, filters: dict) -> list:
        """
        组合筛选：根据多个条件筛选菜品
        
        :param filters: 筛选条件字典，支持的键：
            - canteen_name: 食堂名称
            - window_number: 窗口号
            - meal_type: 餐别
            - min_L1, max_L1: L1 范围
            - min_L2, max_L2: L2 范围
            - min_L3, max_L3: L3 范围
            - min_L4, max_L4: L4 范围
            - min_L5_oil, max_L5_oil: L5 油量范围
            - min_L5_salt, max_L5_salt: L5 盐量范围
        :return: 匹配的菜品列表
        """
        results = self.collection.get()
        
        matched_dishes = []
        
        for meta in results["metadatas"]:
            match = True
            
            # 基本筛选
            if filters.get("canteen_name") and meta.get("canteen_name") != filters["canteen_name"]:
                match = False
            if filters.get("window_number") and meta.get("window_number") != filters["window_number"]:
                match = False
            if filters.get("meal_type") and meta.get("meal_type") != filters["meal_type"]:
                match = False
            
            # 营养范围筛选
            if match:
                if filters.get("min_L1") is not None and meta.get("L1", 0) < filters["min_L1"]:
                    match = False
                if filters.get("max_L1") is not None and meta.get("L1", 0) > filters["max_L1"]:
                    match = False
                if filters.get("min_L2") is not None and meta.get("L2", 0) < filters["min_L2"]:
                    match = False
                if filters.get("max_L2") is not None and meta.get("L2", 0) > filters["max_L2"]:
                    match = False
                if filters.get("min_L3") is not None and meta.get("L3", 0) < filters["min_L3"]:
                    match = False
                if filters.get("max_L3") is not None and meta.get("L3", 0) > filters["max_L3"]:
                    match = False
                if filters.get("min_L4") is not None and meta.get("L4", 0) < filters["min_L4"]:
                    match = False
                if filters.get("max_L4") is not None and meta.get("L4", 0) > filters["max_L4"]:
                    match = False
                if filters.get("min_L5_oil") is not None and meta.get("L5_oil", 0) < filters["min_L5_oil"]:
                    match = False
                if filters.get("max_L5_oil") is not None and meta.get("L5_oil", 0) > filters["max_L5_oil"]:
                    match = False
                if filters.get("min_L5_salt") is not None and meta.get("L5_salt", 0) < filters["min_L5_salt"]:
                    match = False
                if filters.get("max_L5_salt") is not None and meta.get("L5_salt", 0) > filters["max_L5_salt"]:
                    match = False
            
            if match:
                matched_dishes.append(meta)
        
        return matched_dishes

    def clear_database(self):
        """
        清空数据库中的所有数据
        
        :return: 操作结果消息
        """
        try:
            results = self.collection.get()
            ids = results["ids"]
            
            if ids:
                self.collection.delete(ids=ids)
                return f"已成功删除 {len(ids)} 条记录"
            else:
                return "数据库为空，无需删除"
        except Exception as e:
            return f"删除数据时出错: {str(e)}"


if __name__ == "__main__":
    db = CanteenDB()
    clear_result = db.clear_database()
    print(clear_result)

    with open("Nutrition_agent/dish_data/canteen_menu_data_half.json", "r", encoding="utf-8") as f:
        canteen_data = json.load(f)
    result = db.save_canteen_data(canteen_data)
    print(result)
