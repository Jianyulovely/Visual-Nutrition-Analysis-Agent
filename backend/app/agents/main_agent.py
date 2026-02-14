from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.vision_agent import VisionAgent
from app.agents.analysis_agent import AnalysisAgent

# 定义全局统一的状态机模型
class VisionAgentState(TypedDict):
    username: str
    image_path: str
    vision_report: Optional[str]
    analysis_results: Optional[dict]


class VisionAnalysisAgent:
    def __init__(self):
        # 1. 实例化两个独立智能体
        self.vision_agent = VisionAgent()
        self.analysis_agent = AnalysisAgent()
        
        self.checkpointer = MemorySaver()
        # 2. 构建主流程图
        self.graph = self._init_graph()


    def _init_graph(self):
        builder = StateGraph(VisionAgentState)

        # 定义节点：调用子智能体并映射状态
        builder.add_node("vision", lambda state: {
            "vision_report": self.vision_agent.analyze_image(state["image_path"])
        })
        
        # 判断图片是否有效，从而进入分析阶段
        def is_valid_pic(state: VisionAgentState):
            if state["vision_report"].is_valid:
                return "analysis"
            return END
        
        builder.add_node("analysis", lambda state: {
            "analysis_results": self.analysis_agent.analyze(
                state["username"], state["vision_report"].report
            )
        })
     
        # 连接流程
        builder.add_edge(START, "vision")
        builder.add_conditional_edges(
            "vision",
            is_valid_pic,
            {
                "analysis": "analysis",
                "__end__": END
            }
        )
        builder.add_edge("analysis", END)

        return builder.compile(checkpointer=self.checkpointer)

    def run(self, username: str, image_path: str = None, thread_id: str = None):
        """对外统一暴露的封装接口"""
        config = {"configurable": {"thread_id": thread_id}}
        initial_input = {
            "username": username,
            "image_path": image_path,
        }
        return self.graph.invoke(initial_input, config=config)

if __name__ == "__main__":
    agent = VisionAnalysisAgent()
    agent_response = agent.run(username="yjy", image_path="/data3/yjy/envs/agent/agent_codes/Nutrition_agent/food_pic/饺子.jpg") 
    print(agent_response.get("analysis_results", {}).get("final_response"))
