"""
使用llm进一步完善用户上一餐的分析报告，将分析结果存入用户数据库
"""
import json
import operator

from typing import Optional, TypedDict, Annotated, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.agent_utils.agent_prompt import SEARCHING_NODE_PROMPT, SUMMARIZE_NODE_PROMPT
from app.agent_utils.get_llm import get_llm

class AgentState(TypedDict):
    """
    定义Agent的状态
    """
    username: str
    vision_report: str
    extracted_info: str
    messages: Annotated[list, operator.add]
    final_response: str
    retry_count: int  # 记录失败次数，防止搜索或解析陷入死循环
    errors: List[str] # 记录运行中的错误信息，便于调试
    save_status: bool # 新增：用于记录数据库存入状态


class AnalysisAgent:
    def __init__(self):

        self.search_tool = TavilySearchResults(max_results=3)

        # 告诉烹饪智能体有这样一个搜索工具
        self.searching_llm = get_llm().bind_tools(
            [self.search_tool],
            parallel_tool_calls=True
        )

        # 标准化输出智能体只负责标准化输出，不调用搜索工具
        self.summarize_llm = get_llm()

        self.searching_node_prompt = SEARCHING_NODE_PROMPT
        self.summarize_node_prompt = SUMMARIZE_NODE_PROMPT
        
        # 工具节点，用于搜索操作
        self.tool_node = ToolNode([self.search_tool])

        # 初始化工作流图
        self.workflow = self._build_graph()
    

    def _searching_node(self, state: AgentState) -> AgentState:
        """
        搜索节点，根据视觉分析报告内容调用搜索工具，获取菜品的油盐用量
        """

        vision_data = state.get("vision_report", "")
        input_prompt = f"""视觉报告如下：{vision_data}，开始分析油盐含量。"""
        
        if not state.get("messages"):
            # 第一次调用烹饪节点，添加系统提示
            messages = [
                SystemMessage(content=self.searching_node_prompt),
                HumanMessage(content=input_prompt)
            ]
        else:
            # 后续调用，直接添加工具调用结果
            messages = state["messages"]

        response = self.searching_llm.invoke(messages)
        
        return {
            "messages": [response],
            "extracted_info": response.content
        }


    def _summarize_node(self, state: AgentState) -> AgentState:
        """
        将补全的报告结果映射到标准菜单数据json
        """

        dish_knowledge = state["extracted_info"]

        input_prompt = f"""请根据以下事实进行 L1-L5 映射计算：\n{dish_knowledge}"""
        messages = [
            SystemMessage(content=self.summarize_node_prompt),
            HumanMessage(content=input_prompt)
        ]

        response = self.summarize_llm.invoke(messages)

        # 清理 Markdown 代码块标签
        clean_json = response.content.replace("```json", "").replace("```", "").strip()


        return {"final_response": clean_json}


    def _save_node(self, state: AgentState) -> dict:
        """
        将菜单数据存入用户数据库
        """
        try:
            report_data = json.loads(state["final_response"])
            username = state.get("username", "Guest")
            
            # 执行 save_last_dish 操作
            save_result = self.db.save_analysis_report(username, report_data)
            
            # check_save 逻辑：验证返回值是否包含成功信息
            if save_result:
                print(f"【数据库存入成功】用户: {username}, 菜品: {report_data.get('dish_name')}")
                return {"save_status": True}
            else:
                raise Exception("数据库写入返回失败")
                
        except Exception as e:
            error_msg = f"存储检测失败 (check_save): {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": [error_msg], "save_status": False}

    def _build_graph(self):

        builder = StateGraph(AgentState)
        builder.add_node("searching", self._searching_node)
        builder.add_node("tools", self.tool_node)
        builder.add_node("summarize", self._summarize_node)
        
        builder.add_edge(START, "searching")

        builder.add_conditional_edges(
            "searching",              
            should_continue,     
            {                       
                "tools": "tools",  
                "summarize": "summarize"
            }
        )

        # 如果条件边使用了工具，则再次指向cooking节点，重新判定是否需要工具
        builder.add_edge("tools", "searching") # 循环：工具执行完回到搜索节点

        builder.add_edge("summarize", END)

        return builder.compile()

    def analyze(self, username: str, vision_report: str):
        """执行入口"""
        initial_state = {
            "username": username,
            "vision_report": vision_report,
            "messages": [],
            "retry_count": 0,
            "errors": []
        }
        return self.workflow.invoke(initial_state)


# 定义条件边的逻辑函数
def should_continue(state: AgentState) -> str:
    """判断模型是否发起了工具调用"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "summarize"



# 运行逻辑
if __name__ == "__main__":
  
    vision_report = "\n- 类别: 主食\n- 名称: 紫薯块\n- 食材组成: 紫薯 (80g)\n- 视觉特征: 位于透明小碗内，呈长条楔形，横截面约3cm×4cm，高度约5cm，表面光滑无酱汁，颜色深紫带黄心。\n---\n\n---\n- 类别: 菜品\n- 名称: 炒蛋\n- 食材组成: 鸡蛋 (60g)\n- 视觉特征: 位于餐盘左上格，呈不规则折叠块状，覆盖面积约占格位2/3，厚度约1.5cm，表面微焦黄，无油汪或汤汁。\n---\n\n---\n- 类别: 菜品\n- 名称: 西兰花\n- 食材组成: 西兰花 (50g)\n- 视觉特征: 位于餐盘中上格，由3-4个完整花簇堆叠，高度约2cm，占据格位约一半面积，颜色翠绿，茎部可见但未切碎。\n---\n\n---\n- 类别: 菜品\n- 名称: 卤蛋与寿司卷\n- 食材组成: 鸡蛋 (30g), 海苔米饭卷 (40g)\n- 视觉特征: 位于餐盘右上格，含半个卤蛋（蛋白完整、蛋黄微散）与一个小型寿司卷（海苔外裹，内有米饭和少量馅料），两者并列摆放，总占格位约2/3。\n---\n\n---\n- 类别: 菜品\n- 名称: 胡萝卜条\n- 食材组成: 胡萝卜 (70g)\n- 视觉特征: 位于餐盘下大格，共4段圆柱形胡萝卜条，每段长约5cm、直径约2cm，表面微红带光泽，无酱汁附着，排列松散。\n---"
    
    username = "yjy"
    agent = AnalysisAgent()
    agent.analyze(username, vision_report)        