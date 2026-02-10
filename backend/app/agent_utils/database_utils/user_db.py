import chromadb
from datetime import datetime, timedelta
import json
import uuid
import sys
import os

# 添加父目录到 sys.path，以便导入 get_embed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from get_embed import DashScopeEmbeddingAdapter

"""
使用Chroma数据库实现
"""
class UserDB:
    def __init__(self, db_path="/data3/yjy/envs/agent/agent_codes/Nutrition_agent/database/user_diet_chroma"):
        
        self.embedding_fn = DashScopeEmbeddingAdapter()

        # 1. 初始化本地持久化客户端
        self.client = chromadb.PersistentClient(path=db_path)
        # 2. 获取或创建集合（相当于 SQL 的表）
        self.collection = self.client.get_or_create_collection(
            name="user_diet_history",
            embedding_function=self.embedding_fn
        )

    def save_analysis_report(self, username: str, report_json: dict):
        """
        将分析报告存入 Chroma 元数据
        """
        # 生成唯一 ID
        record_id = str(uuid.uuid4())
        
        # 准备元数据 (Chroma metadata 不支持嵌套字典，需转为 JSON 字符串)
        metadata = {
            "username": username,
            "dish_name": report_json["dish_name"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "full_report": json.dumps(report_json, ensure_ascii=False)
        }

        # 存入集合
        self.collection.add(
            ids=[record_id],
            metadatas=[metadata],
            # 存入document时会自动调用embedding_fn
            documents=[report_json["description"]] # 将描述作为文档内容，方便后续语义搜索
        )
        return f"已成功记录 {username} 的历史菜单：{report_json['dish_name']}"

    def get_user_menu_history(self, username: str, k: int = 10):
        """
        获取用户的菜单历史
        """
        results = self.collection.get(
            where={"username": username},
            limit=k
        )
        
        history = []
        for meta in results["metadatas"]:
            history.append({
                "dish_name": meta["dish_name"],
                "created_at": meta["created_at"],
                "report": json.loads(meta["full_report"])
            })
        return history

    def get_nutrition_c_vector(self, username: str, meal_time: str) -> list:
        """
        获取用户指定时间段的营养六维向量
        """
        # 1. 获取该用户所有记录
        results = self.collection.get(where={"username": username})
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        total_vector = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # [L1, L2, L3, L4, oil, salt]

        # 2. 定义时间区间逻辑
        time_ranges = {
            "breakfast": (5, 10),
            "lunch": (10, 15),
            "dinner": (15, 23)
        }
        start_h, end_h = time_ranges.get(meal_time, (0, 0))

        for meta in results["metadatas"]:
            # 过滤日期
            if not meta["created_at"].startswith(today_str):
                continue
            
            # 过滤餐时
            dt = datetime.strptime(meta["created_at"], "%Y-%m-%d %H:%M:%S")
            if not (start_h <= dt.hour < end_h):
                continue
            
            # 累加向量
            report = json.loads(meta["full_report"])
            vector = report.get("pagoda_nutrition_vector", {})
            
            total_vector[0] += vector.get("L1", {}).get("total_value", 0)
            total_vector[1] += vector.get("L2", {}).get("total_value", 0)
            total_vector[2] += vector.get("L3", {}).get("total_value", 0)
            total_vector[3] += vector.get("L4", {}).get("total_value", 0)
            total_vector[4] += vector.get("L5", {}).get("oil", 0)
            total_vector[5] += vector.get("L5", {}).get("salt", 0)

        return total_vector

    def get_menu_ingredients_count(self, record_id: str) -> dict:
        """
        获取指定菜单的食材数量统计
        
        :param record_id: 记录ID
        :return: 食材数量统计字典
        """
        results = self.collection.get(ids=[record_id])
        
        if not results["metadatas"]:
            return {}
        
        report = json.loads(results["metadatas"][0]["full_report"])
        
        count = {
            "main": len(report.get("main_ingredients", [])),
            "seasoning": len(report.get("seasonings", []))
        }
        
        return count

    def get_menu_nutrition_summary(self, record_id: str) -> dict:
        """
        获取指定菜单的营养等级汇总
        
        :param record_id: 记录ID
        :return: 营养等级汇总字典
        """
        results = self.collection.get(ids=[record_id])
        
        if not results["metadatas"]:
            return {}
        
        report = json.loads(results["metadatas"][0]["full_report"])
        vector = report.get("pagoda_nutrition_vector", {})
        
        result = {}
        for level_name, level_data in vector.items():
            if level_name == "L5":
                result[level_name] = {
                    "oil": level_data.get("oil", 0),
                    "salt": level_data.get("salt", 0)
                }
            else:
                result[level_name] = level_data.get("total_value", 0)
        
        return result

    def del_user_menu_history(self, username: str) -> str:
        """
        清除指定用户的所有历史菜单数据
        
        :param username: 用户名
        :return: 操作结果信息
        """
        results = self.collection.get(where={"username": username})
        
        if not results["ids"]:
            return f"用户 {username} 不存在或没有历史菜单数据"
        
        self.collection.delete(ids=results["ids"])
        return f"已成功清除用户 {username} 的所有历史菜单数据"

    def get_user_id(self, username: str) -> str:
        """
        根据用户名获取用户ID
        
        注意：ChromaDB 中用户ID即为记录ID，这里返回第一个匹配记录的ID
        
        :param username: 用户名
        :return: 用户ID（记录ID），如果用户不存在则返回 None
        """
        results = self.collection.get(where={"username": username}, limit=1)
        
        if not results["ids"]:
            return None
        
        return results["ids"][0]

    def clr_db(self):
        """清空数据库"""
        ids = self.collection.get()["ids"]
        if ids:
            self.collection.delete(ids=ids)
        return "数据库已成功清空"

if __name__ == "__main__":

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
    db = UserDB()
    # result = db.save_analysis_report("张三", report_data)
    # print(result)
    c_vector = db.get_nutrition_c_vector("张三", "lunch")
    print(c_vector)
