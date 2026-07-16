from problem.models import VariableType
from problem.shared_utils import has_custom_print

T = "    "


def get_cpp_type(var_type, template_type=None, dimensions=1, is_method_params=False):
    mapping = {
        VariableType.INTEGER: "int",
        VariableType.STRING: "string",
        VariableType.BOOLEAN: "bool",
        VariableType.CHAR: "char",
        VariableType.FLOAT: "double",
        VariableType.LONG: "long long",
    }
    if var_type == VariableType.ARRAY:
        inner = get_cpp_type(template_type)
        for _ in range(dimensions):
            inner = f"vector<{inner}>{ "&" if is_method_params else ""}"
        return inner
    if var_type not in mapping and var_type:
        return f"{var_type}*" if var_type.endswith("Node") else var_type
    return mapping.get(var_type, "int")


def generate_cpp_reader(var_name, template_type, dimensions, depth=1):
    indent = T * depth
    if dimensions == 0:
        return f"{indent}cin >> {var_name};\n"

    code = ""
    safe_name = var_name.replace("[", "_").replace("]", "_")
    code += (
        f"{indent}int n_{safe_name};\n"
        f"{indent}cin >> n_{safe_name};\n"
        f"{indent}{var_name}.resize(n_{safe_name});\n"
    )

    loop_var = f"i{dimensions}"
    code += (
        f"{indent}for(int {loop_var}=0; {loop_var}<n_{safe_name}; {loop_var}++) {{\n"
    )

    if dimensions == 1:
        if template_type == VariableType.STRING:
            code += f"{T * (depth + 1)}getline(cin >> ws, {var_name}[{loop_var}]);\n"
        elif template_type == VariableType.BOOLEAN:
            code += f"{T * (depth + 1)}cin >> boolalpha >> {var_name}[{loop_var}];\n"
        else:
            code += f"{T * (depth + 1)}cin >> {var_name}[{loop_var}];\n"
    else:
        code += generate_cpp_reader(
            f"{var_name}[{loop_var}]", template_type, dimensions - 1, depth + 1
        )

    code += f"{indent}}}\n"
    return code


def _generate_cpp_print_loop(template_type, dimensions, var_name, depth=2):
    indent = T * depth
    loop_var = f"i{dimensions}"
    if dimensions == 1:
        if template_type == VariableType.STRING:
            return (
                f"{indent}for(size_t {loop_var} = 0; {loop_var} < {var_name}.size(); {loop_var}++) {{\n"
                f'{indent}    cout << {var_name}[{loop_var}] << "\\n";\n'
                f"{indent}}}\n"
            )
        elif template_type == VariableType.BOOLEAN:
            return (
                f"{indent}for(size_t {loop_var} = 0; {loop_var} < {var_name}.size(); {loop_var}++) {{\n"
                f'{indent}    if({loop_var} > 0) cout << " ";\n'
                f'{indent}    cout << ({var_name}[{loop_var}] ? "true" : "false");\n'
                f"{indent}}}\n"
            )
        return (
            f"{indent}for(size_t {loop_var} = 0; {loop_var} < {var_name}.size(); {loop_var}++) {{\n"
            f'{indent}    if({loop_var} > 0) cout << " ";\n'
            f"{indent}    cout << {var_name}[{loop_var}];\n"
            f"{indent}}}\n"
        )

    code = (
        f"{indent}for(size_t {loop_var} = 0; {loop_var} < {var_name}.size(); {loop_var}++) {{\n"
        f"{_generate_cpp_print_loop(template_type, dimensions - 1, f'{var_name}[{loop_var}]', depth + 1)}"
        f'{T * (depth + 1)}cout << "\\n";\n'
        f"{indent}}}\n"
    )
    return code


def generate_cpp_inline_print(
    ret_type, template_type, dimensions, var_name="result", depth=2
):
    indent = T * depth
    if ret_type in ["void", "VOID"]:
        return ""
    is_array = ret_type == VariableType.ARRAY or ret_type == "Array"
    if not is_array:
        if ret_type == VariableType.BOOLEAN:
            return f'{indent}cout << ({var_name} ? "true" : "false");\n'
        return f"{indent}cout << {var_name};\n"

    return _generate_cpp_print_loop(template_type, dimensions, var_name, depth)


def _generate_cpp_multi_runner(
    methods, input_output_function, class_name, constructor_method
):
    """Build the C++ runner for multi-method / constructor problems."""
    _1 = T
    _2 = T * 2
    _3 = T * 3
    _4 = T * 4
    runner_code = (
        f"int main() {{\n"
        f"{_1}int T;\n"
        f"{_1}if (!(cin >> T)) return 0;\n"
        f"{_1}for (int _tc = 0; _tc < T; _tc++) {{\n"
        f"{_2}int num_cmds; if (!(cin >> num_cmds)) return 0;\n"
        f"{_2}vector<string> commands(num_cmds);\n"
        f"{_2}for(int i=0; i<num_cmds; i++) getline(cin >> ws, commands[i]);\n"
        f"{_2}int num_outer_args; cin >> num_outer_args;\n"
        f"{_2}vector<string> outputs;\n"
        f"{_2}{class_name}* obj = nullptr;\n"
        f'{_2}cout << "_USER_PRINT_START_" << endl;\n'
        f"{_2}long long _total_t_ns = 0;\n"
        f"{_2}for(int i=0; i<num_cmds; i++) {{\n"
        f"{_3}string cmd = commands[i];\n"
        f"{_3}int arg_len; cin >> arg_len;\n"
    )

    if constructor_method:
        c_inputs = list(constructor_method.parameters.all().order_by("id"))
        runner_code += f'{_3}if (cmd == "{class_name}") {{\n'
        for v in c_inputs:
            if v.type == VariableType.ARRAY:
                runner_code += (
                    f"{_4}{get_cpp_type(v.type, v.template_type, v.array_dimensions)} {v.name};\n"
                    f"{generate_cpp_reader(v.name, v.template_type, v.array_dimensions, depth=4)}"
                )
            elif v.type == VariableType.STRING:
                runner_code += f"{_4}{get_cpp_type(v.type)} {v.name}; getline(cin >> ws, {v.name});\n"
            elif v.type == VariableType.BOOLEAN:
                runner_code += f"{_4}{get_cpp_type(v.type)} {v.name}; cin >> boolalpha >> {v.name};\n"
            else:
                runner_code += (
                    f"{_4}{get_cpp_type(v.type)} {v.name}; cin >> {v.name};\n"
                )
        c_args = ", ".join([v.name for v in c_inputs])
        runner_code += (
            f"{_4}obj = new {class_name}({c_args});\n"
            f'{_4}outputs.push_back("null");\n{_3}}}\n'
        )
    else:
        runner_code += (
            f'{_3}if (cmd == "{class_name}") {{\n'
            f"{_4}obj = new {class_name}();\n"
            f'{_4}outputs.push_back("null");\n{_3}}}\n'
        )

    for method in methods:
        if method.is_constructor:
            continue
        inputs = list(method.parameters.all().order_by("id"))
        runner_code += f'{_3}else if (cmd == "{method.name}") {{\n'
        runner_code += f"{_4}auto _ts = chrono::high_resolution_clock::now();\n"
        for v in inputs:
            if v.type == VariableType.ARRAY:
                runner_code += (
                    f"{_4}{get_cpp_type(v.type, v.template_type, v.array_dimensions)} {v.name};\n"
                    f"{generate_cpp_reader(v.name, v.template_type, v.array_dimensions, depth=4)}"
                )
            elif v.type == VariableType.STRING:
                runner_code += f"{_4}{get_cpp_type(v.type)} {v.name}; getline(cin >> ws, {v.name});\n"
            elif v.type == VariableType.BOOLEAN:
                runner_code += f"{_4}{get_cpp_type(v.type)} {v.name}; cin >> boolalpha >> {v.name};\n"
            else:
                runner_code += (
                    f"{_4}{get_cpp_type(v.type)} {v.name}; cin >> {v.name};\n"
                )
        call = f"obj->{method.name}({', '.join([v.name for v in inputs])})"
        if method.type != "void" and method.type != "VOID":
            runner_code += (
                f"{_4}auto res = {call};\n"
                f"{_4}auto _te = chrono::high_resolution_clock::now();\n"
                f"{_4}_total_t_ns += chrono::duration_cast<chrono::nanoseconds>(_te - _ts).count();\n"
                f"{_4}stringstream ss;\n"
                f"{_4}auto old_buf = cout.rdbuf(ss.rdbuf());\n"
            )
            if has_custom_print(input_output_function, method.type, "CPP"):
                runner_code += f"{_4}print(res);\n"
            else:
                runner_code += generate_cpp_inline_print(
                    method.type,
                    method.template_type,
                    method.array_dimensions,
                    "res",
                    depth=4,
                )
            runner_code += (
                f"{_4}cout.rdbuf(old_buf);\n" f"{_4}outputs.push_back(ss.str());\n"
            )
        else:
            runner_code += (
                f"{_4}{call};\n"
                f"{_4}auto _te = chrono::high_resolution_clock::now();\n"
                f"{_4}_total_t_ns += chrono::duration_cast<chrono::nanoseconds>(_te - _ts).count();\n"
                f'{_4}outputs.push_back("null");\n'
            )
        runner_code += f"{_3}}}\n"

    runner_code += (
        f"{_2}}}\n"
        f'{_2}cout << "_USER_PRINT_END_" << endl;\n'
        f"{_2}long long _tc_t_ns = _total_t_ns;\n"
        f'{_2}cout << "_TIME_" << _tc_t_ns << "_" << endl;\n'
        f'{_2}cout << "[";\n'
        f"{_2}for(size_t i=0; i<outputs.size(); i++) {{\n"
        f'{_3}if (i > 0) cout << ",";\n'
        f"{_3}cout << outputs[i];\n"
        f"{_2}}}\n"
        f'{_2}cout << "]" << endl;\n'
        f"{_2}if (obj) {{ delete obj; obj = nullptr; }}\n"
        f'{_2}cout << "___CODERACER_TC_SEP___" << endl;\n'
        f"{_1}}}\n{_1}return 0;\n}}\n"
    )
    return runner_code


def _generate_cpp_code(
    methods, input_output_function, is_multi, class_name, constructor_method, block
):
    block += f"class {class_name} {{\npublic:\n"
    if is_multi:
        if constructor_method:
            c_inputs = list(constructor_method.parameters.all().order_by("id"))
            c_args = ", ".join(
                f"{get_cpp_type(v.type, v.template_type, v.array_dimensions, is_method_params=True)} {v.name}"
                for v in c_inputs
            )
            block += f"{T}{class_name}({c_args}) {{\n{T * 2}\n{T}}}\n\n"
        else:
            block += f"{T}{class_name}() {{\n{T * 2}\n{T}}}\n\n"

    for method in methods:
        if method.is_constructor:
            continue
        inputs = list(method.parameters.all().order_by("id"))
        ret_type = get_cpp_type(
            method.type, method.template_type, method.array_dimensions
        )
        args = ", ".join(
            f"{get_cpp_type(v.type, v.template_type, v.array_dimensions, is_method_params=True)} {v.name}"
            for v in inputs
        )
        block += f"{T}{ret_type} {method.name}({args}) {{\n{T * 2}// add your method calls here\n{T * 2}\n{T}}}\n"
    block += "};\n"

    if not is_multi and methods:
        method = methods[0]
        inputs = list(method.parameters.all().order_by("id"))
        ret_type = get_cpp_type(
            method.type, method.template_type, method.array_dimensions
        )
        _in = T * 2
        runner_code = (
            f"int main() {{\n"
            f"{T}int T;\n"
            f"{T}if (!(cin >> T)) return 0;\n"
            f"{T}for (int _tc = 0; _tc < T; _tc++) {{\n"
        )
        for v in inputs:
            if v.type == VariableType.ARRAY:
                t = get_cpp_type(
                    VariableType.ARRAY, v.template_type, v.array_dimensions
                )
                runner_code += (
                    f"{_in}{t} {v.name};\n"
                    f"{generate_cpp_reader(v.name, v.template_type, v.array_dimensions, depth=2)}"
                )
            elif (
                v.type not in dict(VariableType.choices)
                and v.type != VariableType.ARRAY
            ):
                t = get_cpp_type(v.type)
                if input_output_function.strip():
                    runner_code += f"{_in}{t} {v.name} = input();\n"
                else:
                    runner_code += f"{_in}{t} {v.name};\n{_in}// TODO: Implement parsing logic for custom type {v.type}\n"
            else:
                t_cpp = get_cpp_type(v.type, v.template_type, v.array_dimensions)
                runner_code += f"{_in}{t_cpp} {v.name};\n"
                if v.type == VariableType.STRING:
                    runner_code += f"{_in}getline(cin >> ws, {v.name});\n"
                elif v.type == VariableType.BOOLEAN:
                    runner_code += f"{_in}cin >> boolalpha >> {v.name};\n"
                else:
                    runner_code += f"{_in}cin >> {v.name};\n"

        call = f"sol.{method.name}({', '.join([v.name for v in inputs])})"
        runner_code += f"\n{_in}{class_name} sol;\n"
        if method.type != "void" and method.type != "VOID" and ret_type != "void":
            runner_code += (
                f'{_in}cout << "_USER_PRINT_START_" << endl;\n'
                f"{_in}auto _t0 = chrono::high_resolution_clock::now();\n"
                f"{_in}{ret_type} result = {call};\n"
                f"{_in}auto _t1 = chrono::high_resolution_clock::now();\n"
                f"{_in}auto _tc_t_ns = chrono::duration_cast<chrono::nanoseconds>(_t1 - _t0).count();\n"
                f'{_in}cout << "_USER_PRINT_END_" << endl;\n'
                f'{_in}cout << "_TIME_" << _tc_t_ns << "_" << endl;\n'
            )
            if has_custom_print(input_output_function, method.type, "CPP"):
                runner_code += f"{_in}print(result);\n{_in}cout << endl;\n"
            else:
                runner_code += generate_cpp_inline_print(
                    method.type,
                    method.template_type,
                    method.array_dimensions,
                    "result",
                    depth=2,
                )
                runner_code += f"{_in}cout << endl;\n"
        else:
            runner_code += (
                f'{_in}cout << "_USER_PRINT_START_" << endl;\n'
                f"{_in}auto _t0 = chrono::high_resolution_clock::now();\n"
                f"{_in}{call};\n"
                f"{_in}auto _t1 = chrono::high_resolution_clock::now();\n"
                f"{_in}auto _tc_t_ns = chrono::duration_cast<chrono::nanoseconds>(_t1 - _t0).count();\n"
                f'{_in}cout << "_USER_PRINT_END_" << endl;\n'
                f'{_in}cout << "_TIME_" << _tc_t_ns << "_" << endl;\n'
            )
        runner_code += (
            f'{_in}cout << "___CODERACER_TC_SEP___" << endl;\n'
            f"{T}}}\n{T}return 0;\n}}\n"
        )
    elif is_multi:
        runner_code = _generate_cpp_multi_runner(
            methods, input_output_function, class_name, constructor_method
        )
    else:
        runner_code = "int main() { return 0; }"

    return runner_code, block
