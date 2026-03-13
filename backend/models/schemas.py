from __future__ import annotations

import operator
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── 1. 视觉节点输出 ──────────────────────────────────────────────
class VisionResponse(BaseModel):
    is_valid: bool = Field(description="图片是否清晰且包含食物")
    reason: str = Field(description="如果不合法，说明原因（如：图片模糊、非食物、无图片）")
    report: str = Field(description="识别到的食材详细报告，若不合法则为空")


# ── 2. 营养宝塔各层结构 ──────────────────────────────────────────
class L5Detail(BaseModel):
    oil: float = 0.0
    salt: float = 0.0


class PagodaLayer(BaseModel):
    total_value: float = 0.0
    ingredients: List[str] = []
    details: dict = {}


class PagodaNutritionVector(BaseModel):
    L1: PagodaLayer = Field(default_factory=PagodaLayer)
    L2: PagodaLayer = Field(default_factory=PagodaLayer)
    L3: PagodaLayer = Field(default_factory=PagodaLayer)
    L4: PagodaLayer = Field(default_factory=PagodaLayer)
    L5: L5Detail = Field(default_factory=L5Detail)


# ── 3. 分析节点最终输出（替代原来的 JSON 字符串）────────────────
class NutritionReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dish_name: str = ""
    main_ingredients: List[str] = []
    seasonings: List[str] = []
    pagoda_nutrition_vector: PagodaNutritionVector = Field(
        default_factory=PagodaNutritionVector
    )
    feature_tags: List[str] = []
    description: str = ""


# ── 4. 主图谱 LangGraph 状态（替代 VisionAgentState TypedDict）──
class VisionAgentState(BaseModel):
    username: str = ""
    image_path: str = ""
    error_reason: Optional[str] = None
    vision_report: Optional[VisionResponse] = None
    analysis_results: Optional[NutritionReport] = None


# ── 5. 分析子图 LangGraph 状态（替代 AgentState TypedDict）──────
class AnalysisState(BaseModel):
    username: str = ""
    vision_report: str = ""
    extracted_info: str = ""
    messages: Annotated[list, operator.add] = []
    final_response: Optional[NutritionReport] = None
    retry_count: int = 0
    errors: List[str] = []
    save_status: bool = False


# ── 6. 统一 API 响应格式 ─────────────────────────────────────────
class ApiResponse(BaseModel):
    status: str
    message: str = ""
    data: Optional[dict] = None
