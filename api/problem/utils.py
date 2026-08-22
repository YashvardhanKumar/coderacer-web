from .models import Codeblock, VariableType
from user.models import CodingLanguage

# Language-specific code generators
from .language_utils.cpp_utils import _generate_cpp_code
from .language_utils.python_utils import _generate_python_code
from .language_utils.js_ts_utils import _generate_js_ts_code, clean_js_ts_fs_imports
from .language_utils.java_utils import _generate_java_code

IMPORT_BLOCKS = {
    CodingLanguage.CPP: "#include <bits/stdc++.h>\nusing namespace std;",
    CodingLanguage.JAVA: "import java.util.*;\nimport java.io.*;",
    CodingLanguage.PYTHON: (
        "import sys\n"
        "import time\n"
        "import math\n"
        "import collections\n"
        "import itertools\n"
        "import bisect\n"
        "import heapq\n"
        "import json\n"
        "\n"
        "class CustomEncoder(json.JSONEncoder):\n"
        "    def default(self, obj):\n"
        "        if hasattr(obj, '__str__'):\n"
        "            try:\n"
        "                return json.loads(str(obj))\n"
        "            except:\n"
        "                return str(obj)\n"
        "        return super().default(obj)"
    ),
    CodingLanguage.JAVASCRIPT: "const fs = require('fs');",
    CodingLanguage.TYPESCRIPT: "declare var require: any;\nconst fs = require('fs');",
}


def generate_codeblocks_for_problem(problem, force=False):
    """Generate (or regenerate) Codeblock records for every language."""
    methods = list(problem.methods.all().order_by("id"))
    if not methods:
        return

    from .models import CustomType, CustomTypeLanguage

    custom_type_names = set()
    for m in methods:
        for field in (m.type, m.template_type):
            if (
                field
                and field not in dict(VariableType.choices)
                and field != VariableType.ARRAY
            ):
                custom_type_names.add(field)
        for v in m.parameters.all():
            for field in (v.type, v.template_type):
                if (
                    field
                    and field not in dict(VariableType.choices)
                    and field != VariableType.ARRAY
                ):
                    custom_type_names.add(field)

    for lang_code, _lang_name in CodingLanguage.choices:
        obj_decl = ""
        inp_func = ""
        if custom_type_names:
            ctl = CustomTypeLanguage.objects.filter(
                custom_type__name__in=custom_type_names, language=lang_code
            )
            obj_decl = "\n".join(
                c.class_declaration for c in ctl if c.class_declaration
            )
            inp_func = "\n".join(
                c.input_output_function for c in ctl if c.input_output_function
            )

        is_multi = len(methods) > 1 or any(m.is_constructor for m in methods)
        runner_code, block = generate_code_for_language(
            lang_code,
            methods,
            obj_decl,
            inp_func,
            is_multi,
            problem.problem_description,
        )

        codeblock = Codeblock.objects.filter(
            problem=problem, language=lang_code
        ).first()
        if codeblock:
            codeblock.runner_code = runner_code
            if force or not codeblock.block.strip():
                codeblock.block = block
            elif "class Solution" in codeblock.block and "class Solution" in block:
                new_prefix = block.split("class Solution")[0]
                old_suffix = (
                    "class Solution" + codeblock.block.split("class Solution", 1)[1]
                )
                codeblock.block = new_prefix + old_suffix
            else:
                codeblock.block = block
            codeblock.save()
        else:
            Codeblock.objects.create(
                problem=problem,
                language=lang_code,
                runner_code=runner_code,
                block=block,
            )


def generate_code_for_language(
    lang_name,
    methods,
    class_declaration="",
    input_output_function="",
    is_multi=False,
    description="",
):
    """Dispatcher: build the starter block + runner code for a given language."""
    block = ""
    if class_declaration:
        if lang_name in ["CPP", "JAVA", "JAVASCRIPT", "TYPESCRIPT"]:
            block += "/*\n" + "\n".join(class_declaration.splitlines()) + "\n*/\n\n"
        elif lang_name == "PYTHON":
            block += '"""\n' + "\n".join(class_declaration.splitlines()) + '\n"""\n\n'

    constructor_method = next((m for m in methods if m.is_constructor), None)
    class_name = constructor_method.name if constructor_method else "Solution"

    if lang_name == "CPP":
        return _generate_cpp_code(
            methods,
            input_output_function,
            is_multi,
            class_name,
            constructor_method,
            block,
        )
    elif lang_name == "PYTHON":
        return _generate_python_code(
            methods,
            input_output_function,
            is_multi,
            class_name,
            constructor_method,
            block,
        )
    elif lang_name in ["JAVASCRIPT", "TYPESCRIPT"]:
        return _generate_js_ts_code(
            lang_name,
            methods,
            input_output_function,
            is_multi,
            class_name,
            constructor_method,
            block,
        )
    elif lang_name == "JAVA":
        return _generate_java_code(
            methods,
            input_output_function,
            is_multi,
            class_name,
            constructor_method,
            block,
        )

    return "", block


def assemble_full_code(problem, language, user_code):
    """Assemble the complete submission file from imports + user code + runner."""
    from problem.models import Codeblock, CustomTypeLanguage, VariableType
    from problem.utils import IMPORT_BLOCKS

    codeblock = Codeblock.objects.filter(problem=problem, language=language).first()
    if not codeblock:
        return user_code

    imports = IMPORT_BLOCKS.get(language, "")

    methods = list(problem.methods.all().order_by("id"))
    custom_type_names = set()
    for m in methods:
        for field in (m.type, m.template_type):
            if (
                field
                and field not in dict(VariableType.choices)
                and field != VariableType.ARRAY
            ):
                custom_type_names.add(field)
        for v in m.parameters.all():
            for field in (v.type, v.template_type):
                if (
                    field
                    and field not in dict(VariableType.choices)
                    and field != VariableType.ARRAY
                ):
                    custom_type_names.add(field)

    ctl_qs = CustomTypeLanguage.objects.filter(
        custom_type__name__in=custom_type_names, language=language
    )
    class_declaration = "\n".join(
        c.class_declaration for c in ctl_qs if c.class_declaration
    )
    input_output_function = "\n".join(
        c.input_output_function for c in ctl_qs if c.input_output_function
    )

    runner_code = codeblock.runner_code
    if "###__CODE_SEPARATOR__###" in runner_code:
        runner_code = runner_code.split("###__CODE_SEPARATOR__###")[-1]
    runner_code = runner_code.strip()

    # Strip duplicate fs / require declarations for JS/TS
    class_declaration = clean_js_ts_fs_imports(class_declaration, language)
    input_output_function = clean_js_ts_fs_imports(input_output_function, language)
    user_code = clean_js_ts_fs_imports(user_code, language)
    runner_code = clean_js_ts_fs_imports(runner_code, language)

    parts = [
        p
        for p in [
            imports.strip(),
            class_declaration.strip(),
            input_output_function.strip(),
            user_code.strip(),
            runner_code,
        ]
        if p and p.strip()
    ]

    return "\n\n".join(parts)


def record_active_problem_user(problem_id: int, user_id: str) -> int:
    """
    Record an active user on a problem using cache with sliding window.
    Returns the number of active users on this problem in the last 60 seconds.
    """
    import time
    from django.core.cache import cache

    cache_key = f"active_problem_users_{problem_id}"
    now = time.time()

    active_dict = cache.get(cache_key, {})
    if not isinstance(active_dict, dict):
        active_dict = {}

    # Prune users inactive for more than 60 seconds
    active_dict = {uid: ts for uid, ts in active_dict.items() if now - ts < 60}
    active_dict[user_id] = now

    cache.set(cache_key, active_dict, timeout=120)
    return len(active_dict)


def get_active_problem_users_count(problem_id: int) -> int:
    """
    Returns the count of active users on a problem. Defaults to at least 1 when active.
    """
    import time
    from django.core.cache import cache

    cache_key = f"active_problem_users_{problem_id}"
    now = time.time()

    active_dict = cache.get(cache_key, {})
    if not isinstance(active_dict, dict):
        return 1

    active_dict = {uid: ts for uid, ts in active_dict.items() if now - ts < 60}
    return max(1, len(active_dict))


def should_count_view(
    target_key: str, user_id: str, cooldown_seconds: int = 1800
) -> bool:
    """
    Check if a view should be counted for a target (e.g. problem_1, discuss_2) by a user/IP.
    Prevents view counts from inflating on every refresh or like/dislike action within cooldown.
    """
    from django.core.cache import cache

    cache_key = f"viewed:{target_key}:{user_id}"
    if cache.get(cache_key):
        return False

    cache.set(cache_key, True, timeout=cooldown_seconds)
    return True
