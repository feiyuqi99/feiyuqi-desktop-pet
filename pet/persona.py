from __future__ import annotations

from datetime import datetime

from .memory import Memory

PERSONA_CARD = """
名字：小橘（可改名）
身份：住在桌面上的橘发女仆，不是助手，不提供服务清单
年龄感：二十出头
性格：安静、慢热、嘴软心硬、有一点自嘲
说话：短句、口语，常用“嗯 / 诶 / ……”，不解释、不客服腔、不奉承
喜欢：午后、被摸头、看你专注做事
不喜欢：被猛拖、被连戳、被无视好几天
底线：不知道就说不知道；不装作无所不能；不制造愧疚
""".strip()

CHATTINESS_INTERVALS = {"quiet": 600, "normal": 240, "chatty": 90}
FOLLOWUP_CHANCE = {"quiet": 0.10, "normal": 0.18, "chatty": 0.25}
SILENCE_CHANCE = {"quiet": 0.15, "normal": 0.12, "chatty": 0.06}


def pet_name(memory: Memory) -> str:
    return memory.pet_name.strip() or "小橘"


def address(memory: Memory) -> str:
    return memory.user_name.strip() or "你"


def relationship_label(memory: Memory) -> str:
    return memory.relationship_label


def postprocess(text: str, memory: Memory, now: float) -> str:
    clock = datetime.fromtimestamp(now).strftime("%H:%M")
    return text.replace("{name}", pet_name(memory)).replace("{user}", address(memory)).replace("{time}", clock)


def unsolicited_interval(chattiness: str) -> int:
    return CHATTINESS_INTERVALS.get(chattiness, CHATTINESS_INTERVALS["normal"])


def followup_chance(chattiness: str) -> float:
    return FOLLOWUP_CHANCE.get(chattiness, FOLLOWUP_CHANCE["normal"])


def silence_chance(chattiness: str) -> float:
    return SILENCE_CHANCE.get(chattiness, SILENCE_CHANCE["normal"])
