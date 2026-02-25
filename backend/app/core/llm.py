from typing import List, Dict
from volcenginesdkarkruntime import Ark

from app.core.config import settings

def _get_client():
    if not settings.ark_api_key:
        return None
    return Ark(
        base_url=settings.ark_api_base,
        api_key=settings.ark_api_key,
    )

async def generate_reason(prompt: str, fallback: str) -> str:
    client = _get_client()
    if not client:
        return fallback

    try:
        # Note: Ark client is synchronous by default, but we can use it in async context
        # In a high-concurrency production env, consider running this in a thread pool
        # or using an async-compatible client if available.
        response = client.responses.create(
            model=settings.ark_model,
            input=[
                {
                    "role": "system", 
                    "content": "你是推荐系统助手，请给出简洁推荐理由"
                },
                {
                    "role": "user", 
                    "content": prompt
                },
            ],
        )
        # Ark response structure handling
        # SDK 返回的是 Pydantic 模型，直接访问属性
        # 兼容不同版本的 SDK 返回格式
        content = ""
        
        # 1. 尝试从新版 SDK 的 output 字段获取
        if hasattr(response, "output") and response.output:
            for item in response.output:
                if hasattr(item, "content") and item.content:
                    for part in item.content:
                        if hasattr(part, "text") and part.text:
                            content = part.text
                            break
                if content:
                    break

        # 2. 如果没拿到，尝试从旧版 choices 字段获取
        if not content and hasattr(response, "choices") and response.choices:
             choice = response.choices[0]
             if hasattr(choice, "message"):
                 content = choice.message.content
             else:
                 content = getattr(choice, "message", {}).get("content")

        return content.strip() if content else fallback
            
    except Exception as e:
        print(f"[LLM Error] generate_reason failed: {e}")
        return fallback
    return fallback

async def generate_reviews(count: int, product_type: str) -> List[Dict[str, str]]:
    """Generates a batch of diverse reviews for a product type."""
    client = _get_client()
    if not client:
        return []

    prompt = (
        f"请为{product_type}生成{count}条中文商品评论。每条评论应包含两部分：1. reviewText（评论正文，50字以内），2. summary（标题，10字以内）。"
        f"评论情感要多样化（正面为主，少量中立），涵盖性能、外观、性价比等维度。"
        f"请直接以JSON数组格式返回，例如：[{{'reviewText': '...', 'summary': '...'}}, ...]。"
        f"不要包含任何Markdown代码块标记或额外说明文字，仅返回纯JSON数组。"
    )

    try:
        response = client.responses.create(
            model=settings.ark_model,
            input=[
                {
                    "role": "system", 
                    "content": "你是电商评论生成助手，请直接输出合法的JSON数组，不要输出任何其他文本。"
                },
                {
                    "role": "user", 
                    "content": prompt
                },
            ],
            temperature=1.5,
        )
        print(f"[LLM Debug] Raw response: {response}")
        
        # 兼容不同版本的 SDK 返回格式
        content = ""
        
        # 1. 尝试从新版 SDK 的 output 字段获取 (ResponseOutputMessage -> ResponseOutputText)
        if hasattr(response, "output") and response.output:
            for item in response.output:
                # 检查是否是消息类型的输出
                if hasattr(item, "role") and item.role == "assistant" and hasattr(item, "content"):
                    for part in item.content:
                        if hasattr(part, "text") and part.text:
                            content = part.text
                            break
                if content:
                    break

        # 2. 如果没拿到，尝试从旧版 choices 字段获取
        if not content and hasattr(response, "choices") and response.choices:
             choice = response.choices[0]
             if hasattr(choice, "message"):
                 if hasattr(choice.message, "content"):
                     content = choice.message.content
             else:
                 content = getattr(choice, "message", {}).get("content")
        
        if not content:
            return []
            
        # Clean up potential markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        import json
        reviews = json.loads(content)
        if isinstance(reviews, list):
            return reviews
        return []
            
    except Exception as e:
        print(f"[LLM Error] generate_reviews failed: {e}")
        return []

