from __future__ import annotations

from copy import deepcopy
from typing import Any


class EvaluatorContractError(RuntimeError):
    """Raised when the base evaluator payload cannot be strengthened safely."""


def strengthen_evaluator_payload(payload: dict[str, Any]) -> dict[str, Any]:
    strengthened = deepcopy(payload)
    try:
        system_message = strengthened["messages"][0]
        user_content = strengthened["messages"][1]["content"]
        prompt_item = user_content[0]
        image_item = user_content[1]
        properties = strengthened["response_format"]["json_schema"]["schema"][
            "properties"
        ]
    except (KeyError, IndexError, TypeError) as exc:
        raise EvaluatorContractError(
            "base evaluator payload has an unsupported structure"
        ) from exc

    if not isinstance(system_message.get("content"), str):
        raise EvaluatorContractError("evaluator system message must be text")
    if not isinstance(prompt_item.get("text"), str):
        raise EvaluatorContractError("evaluator user prompt must be text")
    image_url = image_item.get("image_url")
    if not isinstance(image_url, dict):
        raise EvaluatorContractError("evaluator image item is missing image_url")
    form_schema = properties.get("formVisible")
    if not isinstance(form_schema, dict):
        raise EvaluatorContractError("evaluator schema is missing formVisible")

    system_message["content"] += (
        " Inspect visible controls literally rather than inferring that a "
        "successful submission removed them."
    )
    prompt_item["text"] += (
        " For formVisible, return true when both a labeled text input and a "
        "submit button remain visible after submission, even when a success "
        "state is also visible."
    )
    image_url["detail"] = "high"
    form_schema["description"] = (
        "True when both a labeled text input and a submit button are visibly "
        "present in the post-submission screenshot."
    )
    return strengthened
