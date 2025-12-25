"""AI 语音助手接口 - 使用大模型解析用户语音指令"""
import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.crud import project as crud_project
from app.crud import score as crud_score
from app.models.user import User

router = APIRouter()
settings = get_settings()


class VoiceCommandRequest(BaseModel):
    """语音指令请求"""
    text: str  # 用户语音转文字后的内容


class ParsedIntent(BaseModel):
    """解析后的意图"""
    action: str  # "add_task" | "exchange_points" | "unknown"
    confidence: float  # 置信度 0-1
    data: Dict[str, Any]  # 解析出的数据
    message: Optional[str] = None  # 给用户的提示消息
    warnings: List[str] = []  # 警告信息（如找不到匹配项）


class VoiceCommandResponse(BaseModel):
    """语音指令响应"""
    success: bool
    intent: Optional[ParsedIntent] = None
    error: Optional[str] = None


# 基础系统提示词（不包含硬编码的选项）
SYSTEM_PROMPT = """你是一个积分管理系统的智能助手，负责解析用户的语音指令。

**重要：用户输入是语音识别的结果，可能存在识别错误，你需要智能纠错！**

用户可能的意图：
1. **新增任务** (action: "add_task")
   - 用户会说类似"语文单元形评获得A*，奖励10积分"
   - 需要解析：一级项目名称、二级项目名称（可选）、任务状态、评分等级、惩奖类型、奖励积分或惩罚选项
   
2. **积分兑换** (action: "exchange_points")  
   - 用户会说类似"积分兑换10元"、"兑换20元"
   - 需要解析：奖励名称或金额

请根据用户输入，**先进行语音纠错**，然后返回 JSON 格式的解析结果：
{
  "action": "add_task" 或 "exchange_points" 或 "unknown",
  "confidence": 0.0-1.0 的置信度,
  "corrected_text": "纠错后的文本（你理解的用户真正想说的话）",
  "data": {
    // 对于 add_task:
    "project_level1_name": "一级项目名称",
    "project_level2_name": "二级项目名称（可选，可为null）",
    "status": "任务状态（可选，默认为'completed'）",
    "rating": "评分等级",
    "reward_type": "惩奖类型（'none'、'reward'、'punish'）",
    "reward_points": 数字（奖励积分，当reward_type为'reward'时，**必须使用用户实际说的数值，不要强制匹配到预设值**）,
    "punishment_option_name": "惩罚选项名称（当reward_type为'punish'时）",
    
    // 对于 exchange_points:
    "reward_name": "奖励名称或描述"
  },
  "message": "给用户的友好提示（如果生成message，对于add_task，应使用'将为您记录'而不是'已为您记录'，因为任务还未真正创建）"
}

注意：
- **重要：下方会提供用户系统中所有可用的选项列表（包括固定的枚举值和用户自定义的选项）**
- **项目匹配原则：**
  - **优先匹配语义相近的项目**：如果语音识别有错误但含义相近，可以智能纠错。例如用户自定义了"单元形评"，语音识别为"单元行苹"，应该识别为"单元形评"
  - **不要强行匹配含义相差较远的项目**：如果用户说的项目与现有项目含义相差较远（例如"国际象棋比赛"与"挑战新领域"的"绝地反击"），**不要强行匹配**，应该保留用户原始说的项目名称，让系统提示用户新增项目
  - **匹配标准**：只有当项目名称在语义上真正相关或相似时，才进行匹配。如果只是语音识别错误但含义相同，可以纠错；如果含义完全不同，必须保留原始名称
- **对于奖励积分（reward_points）：必须使用用户实际说的数值，不要强制匹配到预设值！**
  - 如果用户说"奖励15分"，即使15不在预设列表中，也要返回 reward_points: 15
  - 如果用户说"奖励10分"，返回 reward_points: 10
  - 不要因为预设值中有10，就把用户说的15改成10
- **对于message字段：如果生成提示信息，对于add_task操作，必须使用"将为您记录"而不是"已为您记录"，因为任务还未真正创建，只是准备创建**
- 如果完全无法理解，返回 action: "unknown"
- 只返回 JSON，不要有其他内容"""


async def _build_user_context(db: AsyncSession, user_id: int) -> str:
    """
    构建用户上下文信息，包含所有表单下拉框选项
    通过调用后端接口动态获取，确保选项变化时 AI 也能自动适应
    """
    from app.core.enums import (
        TaskStatus,
        TaskRating,
        RewardType,
        get_enum_label,
    )
    
    context_parts = []
    
    # ========== 1. 获取用户自定义的项目（一级和二级） ==========
    level1_projects = await crud_project.get_projects_by_user(db, user_id=user_id, level=1)
    if level1_projects:
        projects_info = []
        for p1 in level1_projects:
            level2_projects = await crud_project.get_projects_by_user(
                db, user_id=user_id, level=2, parent_id=p1.id
            )
            if level2_projects:
                level2_names = [p2.name for p2 in level2_projects]
                projects_info.append(f"  - {p1.name}：{', '.join(level2_names)}")
            else:
                projects_info.append(f"  - {p1.name}")
        
        context_parts.append("【一级项目（用户自定义）】")
        context_parts.extend(projects_info)
    
    # ========== 2. 获取固定的枚举选项（通过枚举接口） ==========
    
    # 任务状态选项
    task_status_options = [
        get_enum_label("task_status", status.value) 
        for status in TaskStatus
    ]
    if task_status_options:
        context_parts.append("\n【任务状态（固定选项）】")
        context_parts.append(f"  {', '.join(task_status_options)}")
    
    # 任务评分选项
    task_rating_options = [
        get_enum_label("task_rating", rating.value) 
        for rating in TaskRating
    ]
    if task_rating_options:
        context_parts.append("\n【任务评分（固定选项）】")
        context_parts.append(f"  {', '.join(task_rating_options)}")
    
    # 惩奖类型选项
    reward_type_options = [
        get_enum_label("reward_type", rt.value) 
        for rt in RewardType
    ]
    if reward_type_options:
        context_parts.append("\n【惩奖类型（固定选项）】")
        context_parts.append(f"  {', '.join(reward_type_options)}")
    
    # 奖励积分选项（从枚举接口获取）
    reward_points_options = [1, 3, 5, 7, 10]  # 这些值在 enums.py 中定义
    if reward_points_options:
        points_labels = [f"{p}积分" for p in reward_points_options]
        context_parts.append("\n【奖励积分（固定选项，仅供参考，必须使用用户实际说的数值）】")
        context_parts.append(f"  {', '.join(points_labels)}")
        context_parts.append("  **重要：如果用户说的积分值不在上述列表中，也必须使用用户实际说的数值，不要强制匹配！例如用户说'奖励15分'，即使15不在列表中，也要返回 reward_points: 15**")
    
    # ========== 3. 获取用户自定义的惩罚选项 ==========
    punishment_options = await crud_score.get_punishment_options(db, user_id=user_id)
    if punishment_options:
        punishment_names = [p.name for p in punishment_options]
        context_parts.append("\n【惩罚选项（用户自定义）】")
        context_parts.append(f"  {', '.join(punishment_names)}")
    
    # ========== 4. 获取用户自定义的兑换选项 ==========
    reward_options = await crud_score.get_reward_exchange_options(db, user_id=user_id)
    if reward_options:
        options_info = [f"  - {o.name}（{o.cost_points}积分）" for o in reward_options]
        context_parts.append("\n【可兑换的奖励选项（用户自定义）】")
        context_parts.extend(options_info)
    
    if context_parts:
        return "\n\n**用户系统中所有可用的选项（请优先匹配这些选项，即使语音识别有错误也要智能纠错）：**\n" + "\n".join(context_parts)
    return ""


@router.post("/parse-voice-command", response_model=VoiceCommandResponse)
async def parse_voice_command(
    request: VoiceCommandRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    解析用户语音指令
    
    使用大模型理解用户意图，并匹配系统中的选项
    """
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI 服务未配置，请联系管理员设置 AI_API_KEY"
        )
    
    try:
        # 获取用户自定义的项目和兑换选项作为上下文
        user_context = await _build_user_context(db, current_user.id)
        
        # 构建完整的系统提示词（基础提示词 + 用户上下文）
        full_system_prompt = SYSTEM_PROMPT + user_context
        
        # 初始化 OpenAI 客户端（兼容 DeepSeek/Qwen）
        client = AsyncOpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_BASE_URL,
        )
        
        # 调用大模型
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": request.text}
            ],
            temperature=0.3,  # 低温度以获得更确定的结果
            max_tokens=500,
        )
        
        # 解析大模型返回
        content = response.choices[0].message.content
        
        # 尝试提取 JSON
        try:
            # 尝试直接解析
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从 markdown 代码块中提取
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                # 尝试找到 JSON 对象
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法从响应中提取 JSON")
        
        # 构建意图对象
        data = parsed.get("data", {})
        # 将纠错后的文本添加到 data 中，方便前端显示
        if parsed.get("corrected_text"):
            data["corrected_text"] = parsed.get("corrected_text")
        
        intent = ParsedIntent(
            action=parsed.get("action", "unknown"),
            confidence=parsed.get("confidence", 0.5),
            data=data,
            message=parsed.get("message"),
            warnings=[]
        )
        
        # 根据意图类型进行数据匹配验证
        if intent.action == "add_task":
            intent = await _validate_task_data(db, intent, current_user.id)
        elif intent.action == "exchange_points":
            intent = await _validate_exchange_data(db, intent, current_user.id)
        
        return VoiceCommandResponse(success=True, intent=intent)
        
    except Exception as e:
        return VoiceCommandResponse(
            success=False,
            error=f"解析语音指令失败: {str(e)}"
        )


async def _validate_task_data(
    db: AsyncSession,
    intent: ParsedIntent,
    user_id: int
) -> ParsedIntent:
    """验证任务数据并匹配系统中的项目"""
    data = intent.data
    warnings = []
    
    # 获取所有一级项目
    level1_projects = await crud_project.get_projects_by_user(db, user_id=user_id, level=1)
    
    # 匹配一级项目（使用更严格的匹配策略，避免强行匹配含义相差较远的项目）
    project_level1_name = data.get("project_level1_name", "")
    matched_level1 = None
    
    if project_level1_name:
        # 首先尝试精确匹配或高度相似匹配
        project_lower = project_level1_name.lower().strip()
        for p in level1_projects:
            p_name_lower = p.name.lower().strip()
            # 精确匹配
            if project_lower == p_name_lower:
                matched_level1 = p
                break
            # 如果用户说的名称包含在项目名称中，且长度相近（避免"国际象棋"匹配到"象棋"这种短词）
            if len(project_lower) >= 3 and project_lower in p_name_lower:
                # 检查是否真的是相关项目（避免强行匹配）
                # 如果项目名称明显更长，可能是包含关系，需要更严格判断
                if len(p_name_lower) - len(project_lower) <= 5:  # 允许一定的长度差异
                    matched_level1 = p
                    break
            # 如果项目名称包含在用户说的名称中
            if len(p_name_lower) >= 3 and p_name_lower in project_lower:
                matched_level1 = p
                break
    
    if matched_level1:
        data["project_level1_id"] = matched_level1.id
        data["project_level1_name_matched"] = matched_level1.name
    else:
        # 如果AI已经解析出项目名称但没有匹配到，保留原始名称，提示用户新增
        if project_level1_name:
            warnings.append(f"未找到匹配的一级项目「{project_level1_name}」，将提示您新增该项目")
        data["project_level1_id"] = None
    
    # 匹配二级项目（使用更严格的匹配策略）
    if matched_level1 and data.get("project_level2_name"):
        level2_projects = await crud_project.get_projects_by_user(
            db, user_id=user_id, level=2, parent_id=matched_level1.id
        )
        project_level2_name = data.get("project_level2_name", "")
        matched_level2 = None
        
        if project_level2_name:
            project_lower = project_level2_name.lower().strip()
            for p in level2_projects:
                p_name_lower = p.name.lower().strip()
                # 精确匹配
                if project_lower == p_name_lower:
                    matched_level2 = p
                    break
                # 如果用户说的名称包含在项目名称中，且长度相近
                if len(project_lower) >= 3 and project_lower in p_name_lower:
                    if len(p_name_lower) - len(project_lower) <= 5:
                        matched_level2 = p
                        break
                # 如果项目名称包含在用户说的名称中
                if len(p_name_lower) >= 3 and p_name_lower in project_lower:
                    matched_level2 = p
                    break
        
        if matched_level2:
            data["project_level2_id"] = matched_level2.id
            data["project_level2_name_matched"] = matched_level2.name
        else:
            # 如果AI已经解析出项目名称但没有匹配到，保留原始名称，提示用户新增
            if project_level2_name:
                warnings.append(f"未找到匹配的二级项目「{project_level2_name}」，将提示您新增该项目")
            data["project_level2_id"] = None
    else:
        data["project_level2_id"] = None
    
    # 验证评分等级
    valid_ratings = ["A*", "A", "B", "C", "D", "E", "F"]
    rating_raw = data.get("rating") or ""  # 处理 None 值
    rating = str(rating_raw).upper() if rating_raw else ""
    
    if rating and rating not in valid_ratings:
        # 尝试模糊匹配
        rating_lower = rating.lower()
        if "优" in rating or "a" in rating_lower:
            if "*" in rating or "星" in rating:
                rating = "A*"
            else:
                rating = "A"
        elif "良" in rating or "b" in rating_lower:
            rating = "B"
        elif "中" in rating or "c" in rating_lower:
            rating = "C"
        elif "差" in rating or "d" in rating_lower:
            rating = "D"
        else:
            warnings.append(f"评分等级「{rating_raw}」可能不正确，请确认")
            rating = ""  # 如果无法匹配，设为空字符串
    
    # 如果 rating 为空，不设置（允许为空，因为任务可能不需要评分）
    if rating:
        data["rating"] = rating
    else:
        data["rating"] = None
    
    # 验证奖励积分（不强制匹配，只提示是否匹配预设值）
    reward_points = data.get("reward_points")
    if reward_points is not None:
        try:
            reward_points = int(reward_points)
            # 预设的积分选项（从枚举中获取）
            valid_reward_points = [1, 3, 5, 7, 10]  # 这些值在 enums.py 中定义
            if reward_points not in valid_reward_points:
                # 不在预设列表中，只提示，不强制修改
                warnings.append(f"积分值「{reward_points}」不在预设列表中（预设值：{', '.join(map(str, valid_reward_points))}），将使用您录入的分数")
            # 保留原始值，不强制修改
            data["reward_points"] = reward_points
        except (ValueError, TypeError):
            # 如果无法转换为整数，添加警告但不强制修改
            warnings.append(f"积分值「{data.get('reward_points')}」可能不正确，请确认")
            # 保留原始值，让前端处理
            data["reward_points"] = data.get("reward_points")
    
    # 验证惩罚选项（匹配系统中的惩罚选项）
    punishment_option_name = data.get("punishment_option_name", "")
    if punishment_option_name:
        # 获取所有惩罚选项
        from app.crud import score as crud_score
        punishment_options = await crud_score.get_punishment_options(db, user_id=user_id)
        
        matched_punishment = None
        if punishment_options:
            punishment_lower = punishment_option_name.lower().strip()
            for option in punishment_options:
                option_name_lower = option.name.lower().strip()
                # 精确匹配
                if punishment_lower == option_name_lower:
                    matched_punishment = option
                    break
                # 模糊匹配（包含关系）
                if len(punishment_lower) >= 2 and (
                    punishment_lower in option_name_lower or 
                    option_name_lower in punishment_lower
                ):
                    matched_punishment = option
                    break
        
        if matched_punishment:
            data["punishment_option_id"] = matched_punishment.id
            data["punishment_option_name_matched"] = matched_punishment.name
        else:
            # 如果AI已经解析出惩罚选项名称但没有匹配到，保留原始名称，提示用户新增
            warnings.append(f"未找到匹配的惩罚选项「{punishment_option_name}」，将提示您新增该选项")
            data["punishment_option_id"] = None
    
    intent.data = data
    intent.warnings = warnings
    return intent


async def _validate_exchange_data(
    db: AsyncSession,
    intent: ParsedIntent,
    user_id: int
) -> ParsedIntent:
    """验证兑换数据并匹配系统中的奖励选项"""
    data = intent.data
    warnings = []
    
    # 获取所有奖励选项
    reward_options = await crud_score.get_reward_exchange_options(db, user_id=user_id)
    
    reward_name = data.get("reward_name", "")
    matched_option = None
    
    # 尝试匹配
    for option in reward_options:
        # 精确匹配名称
        if reward_name.lower() == option.name.lower():
            matched_option = option
            break
        # 模糊匹配名称
        if reward_name.lower() in option.name.lower() or option.name.lower() in reward_name.lower():
            matched_option = option
            break
        # 尝试从用户输入中提取数字进行匹配
        numbers = re.findall(r'\d+', reward_name)
        if numbers:
            for num in numbers:
                if num in option.name:
                    matched_option = option
                    break
    
    if matched_option:
        data["reward_option_id"] = matched_option.id
        data["reward_option_name"] = matched_option.name
        data["cost_points"] = matched_option.cost_points
    else:
        warnings.append(f"未找到奖励「{reward_name}」的匹配项，请手动选择")
        data["reward_option_id"] = None
        # 列出可用选项供参考
        if reward_options:
            available = [f"{o.name}({o.cost_points}积分)" for o in reward_options[:5]]
            intent.message = f"可用的兑换选项: {', '.join(available)}"
    
    intent.data = data
    intent.warnings = warnings
    return intent


@router.post("/recognize-audio")
async def recognize_audio(
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    识别音频文件并返回解析结果（用于微信浏览器等不支持 Web Speech API 的环境）
    
    使用 OpenAI Whisper API 进行语音识别，然后解析指令
    """
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI 服务未配置，请联系管理员设置 AI_API_KEY"
        )
    
    try:
        # 读取音频文件
        audio_content = await audio.read()
        
        # 使用 OpenAI Whisper API 进行语音识别
        client = AsyncOpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_BASE_URL,
        )
        
        # 将音频内容转换为文件对象
        import io
        audio_file = io.BytesIO(audio_content)
        audio_file.name = audio.filename or "audio.webm"
        
        # 调用 Whisper API 进行语音识别
        try:
            # 注意：需要 OpenAI API 支持 audio.transcriptions
            # 如果使用 DeepSeek/Qwen，可能需要使用其他语音识别服务
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh"
            )
            text = transcription.text
        except Exception as e:
            # 如果不支持 Whisper，提示用户使用文字输入
            # 未来可以集成百度、讯飞、阿里云等语音识别服务
            raise HTTPException(
                status_code=501,
                detail=f"当前 AI 服务不支持音频识别: {str(e)}。请使用文字输入功能。"
            )
        
        # 使用识别出的文本调用解析接口
        user_context = await _build_user_context(db, current_user.id)
        full_system_prompt = SYSTEM_PROMPT + user_context
        
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        content = response.choices[0].message.content
        
        # 解析 JSON
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                else:
                    raise ValueError("无法从响应中提取 JSON")
        
        data = parsed.get("data", {})
        if parsed.get("corrected_text"):
            data["corrected_text"] = parsed.get("corrected_text")
        
        intent = ParsedIntent(
            action=parsed.get("action", "unknown"),
            confidence=parsed.get("confidence", 0.5),
            data=data,
            message=parsed.get("message"),
            warnings=[]
        )
        
        # 验证数据
        if intent.action == "add_task":
            intent = await _validate_task_data(db, intent, current_user.id)
        elif intent.action == "exchange_points":
            intent = await _validate_exchange_data(db, intent, current_user.id)
        
        return VoiceCommandResponse(
            success=True,
            intent=intent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return VoiceCommandResponse(
            success=False,
            error=f"语音识别失败: {str(e)}"
        )


@router.get("/available-options")
async def get_available_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户可用的选项，供语音助手使用
    返回项目列表和兑换选项列表
    """
    # 获取一级项目
    level1_projects = await crud_project.get_projects_by_user(db, user_id=current_user.id, level=1)
    
    # 获取所有二级项目
    projects_data = []
    for p1 in level1_projects:
        level2_projects = await crud_project.get_projects_by_user(
            db, user_id=current_user.id, level=2, parent_id=p1.id
        )
        projects_data.append({
            "id": p1.id,
            "name": p1.name,
            "level2_projects": [{"id": p2.id, "name": p2.name} for p2 in level2_projects]
        })
    
    # 获取兑换选项
    reward_options = await crud_score.get_reward_exchange_options(db, user_id=current_user.id)
    
    return {
        "projects": projects_data,
        "reward_options": [
            {"id": o.id, "name": o.name, "cost_points": o.cost_points}
            for o in reward_options
        ],
        "ratings": ["A*", "A", "B", "C", "D", "E", "F"],
        "reward_points": [1, 2, 3, 5, 8, 10, 15, 20, 25, 30]
    }

