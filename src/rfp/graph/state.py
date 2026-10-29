from typing import TypedDict
from dataclasses import dataclass
from typing import Any


class BatchState(TypedDict, total=False):
    state_schema_version: str
    graph_version: str
    rules_version: str
    prompt_version: str
    rfp_run_id: str
    owner_hash: str
    input_fingerprint: str
    suppliers: list[dict]
    provider_snapshot: dict
    criteria_snapshot: list[dict]
    criteria_hash: str
    industry_snapshot: dict
    current_supplier_index: int
    scorecards: dict
    current_pages_ref: str
    current_response: dict
    current_card: dict
    calculations: list[dict]
    event_count: int
    attempts: int
    repair_used: bool
    retry_reason: str
    next_action: str
    run_status: str
    fatal_error: dict|None
    result: dict


@dataclass
class RunContext:
    repo: Any
    client: Any
    claim_token: str
