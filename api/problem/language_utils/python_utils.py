from problem.models import VariableType
from problem.shared_utils import has_custom_print

T = "    "


def get_python_type(var_type, template_type=None, array_dimensions=1):
    mapping = {
        VariableType.INTEGER: "int",
        VariableType.STRING: "str",
        VariableType.BOOLEAN: "bool",
        VariableType.CHAR: "str",
        VariableType.FLOAT: "float",
        VariableType.LONG: "int",
    }
    if var_type == VariableType.ARRAY:
        inner = get_python_type(template_type)
        return f"list[{inner}]"
    if var_type in mapping:
        return mapping[var_type]
    return var_type


def _format_py_args(variables):
    return ", ".join(
        f"{v.name}: {get_python_type(v.type, v.template_type, v.array_dimensions)}"
        for v in variables
    )


def _format_py_return(method_type, template_type, array_dimensions):
    if not method_type or method_type in ("void", "VOID"):
        return "None"
    return get_python_type(method_type, template_type, array_dimensions)


def _generate_python_print_loop(template_type, dimensions, var_name, depth=2):
    indent = T * depth
    if dimensions == 1:
        if template_type == VariableType.BOOLEAN:
            return f'{indent}print(" ".join("true" if x else "false" for x in {var_name}))\n'
        return f'{indent}print(" ".join(map(str, {var_name})))\n'

    loop_var = f"row_{dimensions}"
    code = (
        f"{indent}for {loop_var} in {var_name}:\n"
        f"{_generate_python_print_loop(template_type, dimensions - 1, loop_var, depth + 1)}"
    )
    return code


def generate_python_inline_print(
    ret_type, template_type, dimensions, var_name="result", depth=2
):
    indent = T * depth
    if ret_type in ["void", "VOID"]:
        return ""
    is_array = ret_type == VariableType.ARRAY or ret_type == "Array"
    if not is_array:
        if ret_type == VariableType.BOOLEAN:
            return f'{indent}print("true" if {var_name} else "false")\n'
        return f"{indent}print({var_name})\n"

    if dimensions == 1 and template_type == VariableType.STRING:
        return f"{indent}for s in {var_name}:\n{T * (depth + 1)}print(s)\n"

    return _generate_python_print_loop(template_type, dimensions, var_name, depth)


def _generate_python_multi_runner(methods, class_name, constructor_method):
    """Build the Python runner for multi-method / constructor problems."""
    _2 = T * 2
    _3 = T * 3
    _4 = T * 4
    runner_code = (
        f"def main():\n"
        f"{T}input_data = sys.stdin.read().splitlines()\n"
        f"{T}if not input_data: return\n"
        f"{T}T = int(input_data[0].strip())\n"
        f"{T}idx = 1\n"
        f"{T}for _tc in range(T):\n"
        f"{_2}commands = json.loads(input_data[idx].strip()); idx += 1\n"
        f"{_2}args_list = json.loads(input_data[idx].strip()); idx += 1\n"
        f"{_2}outputs = []\n"
        f"{_2}obj = None\n"
        f"{_2}print('_USER_PRINT_START_')\n"
        f"{_2}_total_time_ns = 0\n"
        f"{_2}for cmd, args in zip(commands, args_list):\n"
    )

    if constructor_method:
        runner_code += (
            f"{_3}if cmd == '{class_name}':\n"
            f"{_4}obj = {class_name}(*args)\n"
            f"{_4}outputs.append(None)\n"
        )
    else:
        runner_code += (
            f"{_3}if cmd == '{class_name}':\n"
            f"{_4}obj = {class_name}()\n"
            f"{_4}outputs.append(None)\n"
        )

    for method in methods:
        if method.is_constructor:
            continue
        runner_code += f"{_3}elif cmd == '{method.name}':\n"
        runner_code += f"{_4}__s = time.perf_counter()\n"
        if method.type != "void" and method.type != "VOID" and method.type:
            runner_code += (
                f"{_4}res = obj.{method.name}(*args)\n" f"{_4}outputs.append(res)\n"
            )
        else:
            runner_code += (
                f"{_4}obj.{method.name}(*args)\n" f"{_4}outputs.append(None)\n"
            )
        runner_code += f"{_4}__e = time.perf_counter()\n"
        runner_code += f"{_4}_total_time_ns += (__e - __s) * 1_000_000_000\n"

    runner_code += (
        f"{_2}print('_USER_PRINT_END_')\n"
        f"{_2}tc_time_ns = _total_time_ns\n"
        f"{_2}print(f'_TIME_{{tc_time_ns:.0f}}_')\n"
        f"{_2}print(json.dumps(outputs, separators=(',', ':'), cls=CustomEncoder))\n"
        f'{_2}print("___CODERACER_TC_SEP___")\n\n'
        f"{T}if __name__ == '__main__':\n{T}    main()\n"
    )
    return runner_code


def _generate_python_code(
    methods, input_output_function, is_multi, class_name, constructor_method, block
):
    if is_multi:
        block += f"class {class_name}:\n"
        if constructor_method:
            c_inputs = list(constructor_method.parameters.all().order_by("id"))
            c_args_str = _format_py_args(c_inputs)
            if c_args_str:
                c_args_str = f", {c_args_str}"
            block += f"{T}def __init__(self{c_args_str}):\n{T * 2}pass\n\n"
        else:
            block += f"{T}def __init__(self):\n{T * 2}pass\n\n"

        for method in methods:
            if method.is_constructor:
                continue
            inputs = list(method.parameters.all().order_by("id"))
            args_str = _format_py_args(inputs)
            if args_str:
                args_str = f", {args_str}"
            ret = _format_py_return(
                method.type, method.template_type, method.array_dimensions
            )
            block += f"{T}def {method.name}(self{args_str}) -> {ret}:\n{T * 2}# add your method calls here\n{T * 2}pass\n\n"
        if not methods:
            block += f"{T}pass\n"
    else:
        block += "class Solution:\n"
        for method in methods:
            inputs = list(method.parameters.all().order_by("id"))
            args_str = _format_py_args(inputs)
            if args_str:
                args_str = f", {args_str}"
            ret = _format_py_return(
                method.type, method.template_type, method.array_dimensions
            )
            block += f"{T}def {method.name}(self{args_str}) -> {ret}:\n{T * 2}# add your method calls here\n{T * 2}pass\n\n"
        if not methods:
            block += f"{T}pass\n"

    if not is_multi and methods:
        method = methods[0]
        inputs = list(method.parameters.all().order_by("id"))
        _2 = T * 2
        runner_code = (
            f"def main():\n"
            f"{T}input_data = sys.stdin.read().splitlines()\n"
            f"{T}if not input_data: return\n"
            f"{T}T = int(input_data[0].strip())\n"
            f"{T}idx = 1\n"
            f"{T}for _tc in range(T):\n"
        )
        for v in inputs:
            if (
                v.type not in dict(VariableType.choices)
                and v.type != VariableType.ARRAY
            ):
                if input_output_function.strip():
                    runner_code += f"{_2}{v.name} = input(input_data[idx]); idx += 1\n"
                else:
                    runner_code += f"{_2}{v.name} = None; idx += 1 # TODO: Implement parsing logic for custom type {v.type}\n"
            else:
                runner_code += (
                    f"{_2}{v.name} = json.loads(input_data[idx].strip()); idx += 1\n"
                )

        call = f"sol.{method.name}({', '.join([v.name for v in inputs])})"
        runner_code += f"\n{_2}sol = Solution()\n"
        if method.type != "void" and method.type != "VOID" and method.type:
            runner_code += f'{_2}print("_USER_PRINT_START_")\n'
            runner_code += f"{_2}_start = time.perf_counter()\n"
            runner_code += f"{_2}result = {call}\n"
            runner_code += f"{_2}_end = time.perf_counter()\n"
            runner_code += f"{_2}tc_time_ns = (_end - _start) * 1_000_000_000\n"
            runner_code += f'{_2}print("_USER_PRINT_END_")\n'
            runner_code += f"{_2}print(f'_TIME_{{tc_time_ns:.0f}}_')\n"
            if has_custom_print(input_output_function, method.type, "PYTHON"):
                runner_code += f"{_2}printOutput(result)\n"
            else:
                runner_code += generate_python_inline_print(
                    method.type,
                    method.template_type,
                    method.array_dimensions,
                    "result",
                    depth=2,
                )
        else:
            runner_code += f'{_2}print("_USER_PRINT_START_")\n'
            runner_code += f"{_2}_start = time.perf_counter()\n"
            runner_code += f"{_2}{call}\n"
            runner_code += f"{_2}_end = time.perf_counter()\n"
            runner_code += f"{_2}tc_time_ns = (_end - _start) * 1_000_000_000\n"
            runner_code += f'{_2}print("_USER_PRINT_END_")\n'
            runner_code += f"{_2}print(f'_TIME_{{tc_time_ns:.0f}}_')\n"
        runner_code += (
            f'{_2}print("___CODERACER_TC_SEP___")\n'
            f"\n{T}if __name__ == '__main__':\n{T}    main()\n"
        )
    elif is_multi:
        runner_code = _generate_python_multi_runner(
            methods, class_name, constructor_method
        )
    else:
        runner_code = (
            "def main():\n    pass\n\nif __name__ == '__main__':\n    main()\n"
        )

    return runner_code, block
