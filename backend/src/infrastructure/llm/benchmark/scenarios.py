from __future__ import annotations

import sqlite3

from application.agents.care_context import CareContextBuilder
from application.dto import PetLogAgentInput
from domain.models import CareContext, ShoppingRecommendation
from infrastructure.database import connect
from infrastructure.llm.care_answer.prompt import build_care_answer_messages
from infrastructure.llm.pet_persona.prompt import build_pet_persona_messages
from infrastructure.llm.record_structuring.prompt import build_record_structuring_messages
from infrastructure.llm.shopping_reason.prompt import (
    build_shopping_category_messages,
    build_shopping_selection_messages,
)
from infrastructure.repositories.pet_profile_repository import PetProfileRepository
from infrastructure.repositories.record_repository import RecordRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository
from infrastructure.seed_data import SAMPLE_PET_ID, seed_default_data

# 시나리오 이름 → 앱에서 어느 기능의 LLM 호출인지
SCENARIO_DESCRIPTIONS: dict[str, str] = {
    "record_structuring": "기록 입력 구조화 (POST /records 계열)",
    "care_question": "케어 질문 답변 (AI 케어 패널)",
    "pet_chat": "반려동물 페르소나 대화",
    "shopping_category": "쇼핑 에이전트 1단계: 검색 상품군 결정",
    "shopping_selection": "쇼핑 에이전트 2단계: Top 3 후보 중 선택 + 추천 이유",
}

SAMPLE_RECORD_TEXT = "아침에 사료를 10g씩 두 번 먹었고 산책 30분 했어. 저녁에 한 번 토했어."
SAMPLE_CARE_QUESTION = "요즘 밥을 남기고 한 번 토했는데 병원에 가봐야 할까요?"
SAMPLE_PET_CHAT_MESSAGE = "오늘 산책 재밌었어?"
SAMPLE_SHOPPING_TEXT = "요즘 사료를 자주 남기고 소화가 잘 안 되는 것 같아요."
SAMPLE_SHOPPING_QUERY = "반려동물 저자극 사료"
SAMPLE_SHOPPING_CANDIDATES = (
    ShoppingRecommendation(
        title="저자극 가수분해 사료 2kg",
        product_url="https://example.org/products/1",
        image_url="https://example.org/images/1.jpg",
        mall_name="샘플몰A",
        lowest_price=32000,
        query=SAMPLE_SHOPPING_QUERY,
        reason="",
        id="candidate-1",
        category="사료",
    ),
    ShoppingRecommendation(
        title="소화 케어 습식 사료 12개입",
        product_url="https://example.org/products/2",
        image_url="https://example.org/images/2.jpg",
        mall_name="샘플몰B",
        lowest_price=18900,
        query=SAMPLE_SHOPPING_QUERY,
        reason="",
        id="candidate-2",
        category="사료",
    ),
    ShoppingRecommendation(
        title="그레인프리 연어 사료 1.5kg",
        product_url="https://example.org/products/3",
        image_url="https://example.org/images/3.jpg",
        mall_name="샘플몰C",
        lowest_price=27500,
        query=SAMPLE_SHOPPING_QUERY,
        reason="",
        id="candidate-3",
        category="사료",
    ),
)


def build_scenarios(
    connection: sqlite3.Connection | None = None,
    pet_id: str = SAMPLE_PET_ID,
    lookback_days: int = 30,
) -> dict[str, list[dict[str, str]]]:
    """앱이 실제로 보내는 프롬프트 빌더를 그대로 써서 시나리오별 OpenAI 메시지를 만든다.

    connection이 없으면 in-memory SQLite에 seed 데이터를 넣어 매번 같은 입력으로 측정한다.
    """
    if connection is None:
        connection = connect(":memory:")
        seed_default_data(connection)
    context = _care_context(connection, pet_id, lookback_days)
    pet, records = context.pet, context.recent_records

    langchain_messages = {
        "record_structuring": build_record_structuring_messages(
            PetLogAgentInput(pet=pet, text=SAMPLE_RECORD_TEXT, source="manual")
        ),
        "care_question": build_care_answer_messages(context, SAMPLE_CARE_QUESTION),
        "pet_chat": build_pet_persona_messages(context, SAMPLE_PET_CHAT_MESSAGE),
        "shopping_category": build_shopping_category_messages(pet, SAMPLE_SHOPPING_TEXT, records, ()),
        "shopping_selection": build_shopping_selection_messages(
            pet, SAMPLE_SHOPPING_TEXT, records, (), SAMPLE_SHOPPING_QUERY, SAMPLE_SHOPPING_CANDIDATES
        ),
    }
    return {
        name: [{"role": role, "content": content} for role, content in messages]
        for name, messages in langchain_messages.items()
    }


def _care_context(connection: sqlite3.Connection, pet_id: str, lookback_days: int) -> CareContext:
    return CareContextBuilder(
        pet_profile_reader=PetProfileRepository(connection=connection),
        record_history_reader=RecordRepository(connection=connection),
        schedule_context_reader=ScheduleRepository(connection=connection),
    ).build(pet_id, lookback_days)
