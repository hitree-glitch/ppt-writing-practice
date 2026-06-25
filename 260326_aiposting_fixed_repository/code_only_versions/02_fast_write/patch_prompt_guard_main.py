#!/usr/bin/env python3
"""Patch the main bytecode to remove expiry and ignore unsafe prompt templates.

This keeps the original posting speed/behavior untouched. It only changes:
- check_license(...): always succeeds
- AutomationWorkerTab.__init__(...): ignores custom_prompt_template when it
  does not contain the required "{keyword}" placeholder.
"""

from __future__ import annotations

import marshal
from pathlib import Path
import types


REPO = Path("C:/Users/user/Documents/\ucf54\ub371\uc2a4 \uc800\uc7a5\uc18c/260326_aiposting_fixed_repository")
SOURCE_PYC = REPO / "extracted_260326_aiposting" / "AI\uae00\uc4f0\uae30\uc790\ub3d9\ud654\ubd07_ChatGPT3.pyc"
PATCHED_PYC = REPO / "patched" / "AI\uae00\uc4f0\uae30\uc790\ub3d9\ud654\ubd07_ChatGPT3.pyc"


def code_from_source(source: str, func_name: str, filename: str) -> types.CodeType:
    namespace: dict[str, object] = {}
    compiled = compile(source, filename, "exec")
    exec(compiled, namespace)
    return namespace[func_name].__code__


def replacement_check_license_code() -> types.CodeType:
    source = """
def check_license(show_message, exit_on_fail, timeout):
    return True, 9999, ""
"""
    return code_from_source(source, "check_license", "AI글쓰기자동화봇_ChatGPT3.py")


def replacement_worker_init_code() -> types.CodeType:
    source = r'''
def __init__(
    self,
    keyword,
    id,
    pw,
    gemini_key,
    publish_type,
    publish_date,
    use_image,
    image_model,
    exclude_english_prompt,
    custom_prompt_template,
    custom_image_prompt_template,
    selected_image_preset,
    allow_image_text,
    include_people,
    manual_login,
):
    QThread.__init__(self)
    self.keyword = keyword
    self.id = id
    self.pw = pw
    self.gemini_key = gemini_key
    self.publish_type = publish_type
    self.publish_date = publish_date
    self.is_running = True
    self.generated_text = ""
    self.generated_image_path = ""
    self.use_image = use_image
    self.image_model = image_model
    self.exclude_english_prompt = exclude_english_prompt

    if custom_prompt_template:
        template_text = str(custom_prompt_template)
        if "{keyword}" not in template_text:
            print("[프롬프트] {keyword} 없는 커스텀 프롬프트를 무시하고 기본 프롬프트를 사용합니다.")
            custom_prompt_template = None

    self.custom_prompt_template = custom_prompt_template
    self.custom_image_prompt_template = custom_image_prompt_template
    self.selected_image_preset = selected_image_preset or "실사형"
    self.allow_image_text = allow_image_text
    self.include_people = include_people
    self.manual_login = manual_login
    print(
        f"[AutomationWorkerTab] 초기화: use_image={use_image}, image_model={image_model}, "
        f"custom_prompt_template={'사용' if custom_prompt_template else '기본값'}, "
        f"image_preset={self.selected_image_preset}, allow_image_text={self.allow_image_text}, "
        f"include_people={self.include_people}"
    )
'''
    return code_from_source(source, "__init__", "AI글쓰기자동화봇_ChatGPT3.py")


def is_worker_init(code: types.CodeType) -> bool:
    args = code.co_varnames[: code.co_argcount]
    return (
        code.co_name == "__init__"
        and "custom_prompt_template" in args
        and "gemini_key" in args
        and "manual_login" in args
    )


def replace_code_objects(code: types.CodeType) -> tuple[types.CodeType, dict[str, int]]:
    counts = {"check_license": 0, "worker_init": 0}

    def walk(current: types.CodeType) -> types.CodeType:
        if current.co_name == "check_license":
            counts["check_license"] += 1
            return replacement_check_license_code()
        if is_worker_init(current):
            counts["worker_init"] += 1
            return replacement_worker_init_code()

        new_consts = []
        changed = False
        for const in current.co_consts:
            if isinstance(const, types.CodeType):
                new_const = walk(const)
                new_consts.append(new_const)
                changed = changed or new_const is not const
            else:
                new_consts.append(const)
        if changed:
            return current.replace(co_consts=tuple(new_consts))
        return current

    return walk(code), counts


def main() -> int:
    data = SOURCE_PYC.read_bytes()
    header = data[:16]
    code = marshal.loads(data[16:])
    patched, counts = replace_code_objects(code)
    if counts != {"check_license": 1, "worker_init": 1}:
        raise RuntimeError(f"Unexpected patch counts: {counts}")
    PATCHED_PYC.parent.mkdir(parents=True, exist_ok=True)
    PATCHED_PYC.write_bytes(header + marshal.dumps(patched))
    print(f"patched_main: {PATCHED_PYC}")
    print(f"counts: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
