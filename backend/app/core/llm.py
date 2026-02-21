import httpx

from app.core.config import settings


async def generate_reason(prompt: str, fallback: str) -> str:
    if not settings.modelscope_api_key:
        return fallback
    payload = {
        "model": settings.modelscope_model,
        "messages": [
            {"role": "system", "content": "你是推荐系统助手，请给出简洁推荐理由"},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.modelscope_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                settings.modelscope_api_base, headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            text = message.get("content") or choice.get("text")
            if text:
                return text.strip()
    except Exception:
        return fallback
    return fallback
