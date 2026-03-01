from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.vision_agent import VisionAgent
from app.agents.analysis_agent import AnalysisAgent


class VisionAgentState(TypedDict):
    username: str
    image_path: str
    error_reason: Optional[str]
    vision_report: Optional[str]
    analysis_results: Optional[dict]


class VisionAnalysisAgent:
    def __init__(self):
        self.vision_agent = VisionAgent()
        self.analysis_agent = AnalysisAgent()
        
        self.checkpointer = MemorySaver()
        self.graph = self._init_graph()

    def _vision_node(self, state: VisionAgentState) -> dict:
        vision_result = self.vision_agent.analyze_image(state["image_path"])
        result = {"vision_report": vision_result}
        
        if not vision_result.is_valid:
            result["error_reason"] = vision_result.reason
            print(f"[图片无效] 原因: {vision_result.reason}")
        else:
            result["error_reason"] = None
        
        return result

    def _init_graph(self):
        builder = StateGraph(VisionAgentState)

        builder.add_node("vision", self._vision_node)
        
        def is_valid_pic(state: VisionAgentState):
            if state["vision_report"].is_valid:
                return "analysis"
            return END
        
        builder.add_node("analysis", lambda state: {
            "analysis_results": self.analysis_agent.analyze(
                state["username"], state["vision_report"].report
            )
        })
     
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
        """对外统一暴露的封装接口，返回完整状态（包含错误信息）"""
        config = {"configurable": {"thread_id": thread_id}}
        initial_input = {
            "username": username,
            "image_path": image_path,
        }
        return self.graph.invoke(initial_input, config=config)

if __name__ == "__main__":
    agent = VisionAnalysisAgent()
    agent_response = agent.run(username="yjy", image_path="/data3/yjy/envs/VAA/Vision_Analysis_agent/food_pic/饺子.jpg") 
    print(agent_response)
