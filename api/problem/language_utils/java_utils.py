from problem.models import VariableType
from problem.shared_utils import has_custom_print

T = "    "


def get_java_type(var_type, template_type=None, dimensions=1):
    mapping = {
        VariableType.INTEGER: "int",
        VariableType.STRING: "String",
        VariableType.BOOLEAN: "boolean",
        VariableType.CHAR: "char",
        VariableType.FLOAT: "double",
        VariableType.LONG: "long",
    }
    if var_type == VariableType.ARRAY:
        inner = get_java_type(template_type)
        return f"{inner}{'[]' * dimensions}"
    if var_type not in mapping and var_type:
        return var_type
    return mapping.get(var_type, "int")


def generate_java_reader(var_name, template_type, dimensions, depth=2, is_root=True):
    indent = T * depth
    if dimensions == 0:
        if template_type == VariableType.INTEGER:
            return f"{indent}{var_name} = sc.nextInt();\n"
        elif template_type == VariableType.STRING:
            return f'{indent}sc.skip("\\\\s*");\n{indent}{var_name} = sc.nextLine();\n'
        elif template_type == VariableType.BOOLEAN:
            return f"{indent}{var_name} = sc.nextBoolean();\n"
        else:
            return f"{indent}{var_name} = sc.next();\n"

    code = ""
    safe_name = var_name.replace("[", "_").replace("]", "_")
    code += (
        f"{indent}int n_{safe_name} = sc.nextInt();\n"
        f"{indent}{var_name} = new {get_java_type(template_type)}[n_{safe_name}]{'[]' * (dimensions-1)};\n"
    )

    loop_var = f"i{dimensions}"
    code += (
        f"{indent}for(int {loop_var}=0; {loop_var}<n_{safe_name}; {loop_var}++) {{\n"
    )

    if dimensions == 1:
        if template_type == VariableType.INTEGER:
            code += f"{T * (depth + 1)}{var_name}[{loop_var}] = sc.nextInt();\n"
        elif template_type == VariableType.STRING:
            code += (
                f'{T * (depth + 1)}sc.skip("\\\\s*");\n'
                f"{T * (depth + 1)}{var_name}[{loop_var}] = sc.nextLine();\n"
            )
        else:
            code += f"{T * (depth + 1)}{var_name}[{loop_var}] = sc.next();\n"
    else:
        code += generate_java_reader(
            f"{var_name}[{loop_var}]",
            template_type,
            dimensions - 1,
            depth + 1,
            is_root=False,
        )

    code += f"{indent}}}\n"
    return code


def _generate_java_print_array(template_type, dimensions, var_name, depth):
    indent = T * depth
    loop_var = f"i{dimensions}"
    if dimensions == 1:
        if template_type == VariableType.STRING:
            return (
                f"{T * depth}for (int {loop_var} = 0; {loop_var} < {var_name}.length; {loop_var}++) {{\n"
                f'{indent}    System.out.println({var_name}[{loop_var}] == null ? "null" : {var_name}[{loop_var}]);\n'
                f"{T * depth}}}\n"
            )
        elif template_type == VariableType.BOOLEAN:
            return (
                f"{T * depth}for (int {loop_var} = 0; {loop_var} < {var_name}.length; {loop_var}++) {{\n"
                f'{indent}    if ({loop_var} > 0) System.out.print(" ");\n'
                f'{indent}    System.out.print({var_name}[{loop_var}] ? "true" : "false");\n'
                f"{T * depth}}}\n"
            )
        else:
            return (
                f"{T * depth}for (int {loop_var} = 0; {loop_var} < {var_name}.length; {loop_var}++) {{\n"
                f'{indent}    if ({loop_var} > 0) System.out.print(" ");\n'
                f"{indent}    System.out.print({var_name}[{loop_var}]);\n"
                f"{T * depth}}}\n"
            )

    code = (
        f"{indent}for (int {loop_var} = 0; {loop_var} < {var_name}.length; {loop_var}++) {{\n"
        f"{T * (depth + 1)}if ({var_name}[{loop_var}] == null) {{\n"
        f'{T * (depth + 2)}System.out.println("null");\n'
        f"{T * (depth + 1)}}} else {{\n"
        f"{_generate_java_print_array(template_type, dimensions - 1, f'{var_name}[{loop_var}]', depth + 2)}"
        f"{T * (depth + 2)}System.out.println();\n"
        f"{T * (depth + 1)}}}\n"
        f"{indent}}}\n"
    )
    return code


def generate_java_print_res(ret_type, template_type, dimensions):
    if ret_type in ["void", "VOID"]:
        return ""
    is_array = ret_type == VariableType.ARRAY or ret_type == "Array"
    java_type = get_java_type(ret_type, template_type, dimensions)
    _2 = T * 2
    code = f"{T}static void _print_res({java_type} val) {{\n"

    is_primitive = java_type in ["int", "boolean", "double", "float", "long", "char"]
    if not is_primitive:
        code += (
            f"{_2}if (val == null) {{\n"
            f'{T * 3}System.out.print("null");\n'
            f"{_2}return;\n"
            f"{_2}}}\n"
        )

    if not is_array:
        is_list = "List" in java_type
        if is_list:
            if "List<List<" in java_type or "List<java.util.List" in java_type:
                code += (
                    f"{_2}for (int i = 0; i < val.size(); i++) {{\n"
                    f"{_2}    java.util.List<?> row = val.get(i);\n"
                    f"{_2}    if (row == null) {{\n"
                    f'{T * 3}System.out.println("null");\n'
                    f"{_2}    }} else {{\n"
                    f"{_2}        for (int j = 0; j < row.size(); j++) {{\n"
                    f'{T * 3}            if (j > 0) System.out.print(" ");\n'
                    f"{T * 3}            System.out.print(row.get(j));\n"
                    f"{_2}        }}\n"
                    f"{_2}        System.out.println();\n"
                    f"{_2}    }}\n"
                    f"{_2}}}\n"
                )
            else:
                code += (
                    f"{_2}for (int i = 0; i < val.size(); i++) {{\n"
                    f'{_2}    if (i > 0) System.out.print(" ");\n'
                    f"{_2}    System.out.print(val.get(i));\n"
                    f"{_2}}}\n"
                )
        elif ret_type == VariableType.BOOLEAN:
            code += f'{_2}System.out.print(val ? "true" : "false");\n'
        else:
            code += f"{_2}System.out.print(val);\n"
    else:
        code += _generate_java_print_array(template_type, dimensions, "val", 2)
    code += f"{T}}}\n\n"
    return code


def _generate_java_multi_runner(
    methods, input_output_function, class_name, constructor_method
):
    """Build the Java runner for multi-method / constructor problems."""
    _1 = T
    _2 = T * 2
    _3 = T * 3
    _4 = T * 4
    _5 = T * 5
    runner_code = f"public class Main {{\n"
    distinct_types = []
    seen = set()
    for method in methods:
        if method.is_constructor or method.type in ["void", "VOID"]:
            continue
        type_key = (method.type, method.template_type, method.array_dimensions)
        if type_key not in seen:
            seen.add(type_key)
            distinct_types.append(method)
    for m in distinct_types:
        runner_code += generate_java_print_res(
            m.type, m.template_type, m.array_dimensions
        )

    runner_code += (
        f"{_1}public static void main(String[] args) {{\n"
        f"{_2}Scanner sc = new Scanner(System.in);\n"
        f"{_2}if (!sc.hasNextInt()) return;\n"
        f"{_2}int T = sc.nextInt();\n"
        f"{_2}for (int _tc = 0; _tc < T; _tc++) {{\n"
        f"{_3}if (!sc.hasNextInt()) break;\n"
        f"{_3}int num_cmds = sc.nextInt();\n"
        f"{_3}String[] commands = new String[num_cmds];\n"
        f'{_3}sc.skip("\\\\s*");\n'
        f"{_3}for(int i=0; i<num_cmds; i++) commands[i] = sc.nextLine();\n"
        f"{_3}int num_outer_args = sc.nextInt();\n"
        f"{_3}List<String> outputs = new ArrayList<>();\n"
        f"{_3}{class_name} obj = null;\n"
        f'{_3}System.out.println("_USER_PRINT_START_");\n'
        f"{_3}long _total_t_ns = 0L;\n"
        f"{_3}for(int i=0; i<num_cmds; i++) {{\n"
        f"{_4}String cmd = commands[i];\n"
        f"{_4}int arg_len = sc.nextInt();\n"
    )

    if constructor_method:
        c_inputs = list(constructor_method.parameters.all().order_by("id"))
        runner_code += f'{_4}if (cmd.equals("{class_name}")) {{\n'
        for v in c_inputs:
            if v.type == VariableType.ARRAY:
                runner_code += (
                    f"{_5}{get_java_type(v.type, v.template_type, v.array_dimensions)} {v.name};\n"
                    f"{generate_java_reader(v.name, v.template_type, v.array_dimensions, depth=5, is_root=True)}"
                )
            elif v.type == VariableType.STRING:
                runner_code += f'{_5}sc.skip("\\\\s*");\n{_5}{get_java_type(v.type)} {v.name} = sc.nextLine();\n'
            elif v.type == VariableType.INTEGER:
                runner_code += f"{_5}{get_java_type(v.type)} {v.name} = sc.nextInt();\n"
            elif v.type == VariableType.BOOLEAN:
                runner_code += (
                    f"{_5}{get_java_type(v.type)} {v.name} = sc.nextBoolean();\n"
                )
            else:
                runner_code += f"{_5}{get_java_type(v.type)} {v.name} = sc.next();\n"
        c_args = ", ".join([v.name for v in c_inputs])
        runner_code += (
            f"{_5}obj = new {class_name}({c_args});\n"
            f'{_5}outputs.add("null");\n{_4}}}\n'
        )
    else:
        runner_code += (
            f'{_4}if (cmd.equals("{class_name}")) {{\n'
            f"{_5}obj = new {class_name}();\n"
            f'{_5}outputs.add("null");\n{_4}}}\n'
        )

    for method in methods:
        if method.is_constructor:
            continue
        inputs = list(method.parameters.all().order_by("id"))
        runner_code += f'{_4}else if (cmd.equals("{method.name}")) {{\n'
        runner_code += f"{_5}long _ts = System.nanoTime();\n"
        for v in inputs:
            if v.type == VariableType.ARRAY:
                runner_code += (
                    f"{_5}{get_java_type(v.type, v.template_type, v.array_dimensions)} {v.name};\n"
                    f"{generate_java_reader(v.name, v.template_type, v.array_dimensions, depth=5, is_root=True)}"
                )
            elif v.type == VariableType.STRING:
                runner_code += f'{_5}sc.skip("\\\\s*");\n{_5}{get_java_type(v.type)} {v.name} = sc.nextLine();\n'
            elif v.type == VariableType.INTEGER:
                runner_code += f"{_5}{get_java_type(v.type)} {v.name} = sc.nextInt();\n"
            elif v.type == VariableType.BOOLEAN:
                runner_code += (
                    f"{_5}{get_java_type(v.type)} {v.name} = sc.nextBoolean();\n"
                )
            else:
                runner_code += f"{_5}{get_java_type(v.type)} {v.name} = sc.next();\n"
        call = f"obj.{method.name}({', '.join([v.name for v in inputs])})"
        if method.type != "void" and method.type != "VOID" and method.type:
            runner_code += (
                f"{_5}{get_java_type(method.type, method.template_type, method.array_dimensions)} res = {call};\n"
                f"{_5}long _te = System.nanoTime();\n"
                f"{_5}_total_t_ns += (_te - _ts);\n"
                f"{_5}java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();\n"
                f"{_5}java.io.PrintStream ps = new java.io.PrintStream(baos);\n"
                f"{_5}java.io.PrintStream old = System.out;\n"
                f"{_5}System.setOut(ps);\n"
            )
            if has_custom_print(input_output_function, method.type, "JAVA"):
                runner_code += f"{_5}Parser.print(res);\n"
            else:
                runner_code += f"{_5}_print_res(res);\n"
            runner_code += (
                f"{_5}System.out.flush();\n"
                f"{_5}System.setOut(old);\n"
                f"{_5}outputs.add(baos.toString());\n"
            )
        else:
            runner_code += (
                f"{_5}{call};\n"
                f"{_5}long _te = System.nanoTime();\n"
                f"{_5}_total_t_ns += (_te - _ts);\n"
                f'{_5}outputs.add("null");\n'
            )
        runner_code += f"{_4}}}\n"

    runner_code += (
        f"{_3}}}\n"
        f'{_3}System.out.println("_USER_PRINT_END_");\n'
        f"{_3}long _tc_t_ns = _total_t_ns;\n"
        f'{_3}System.out.println("_TIME_" + _tc_t_ns + "_");\n'
        f'{_3}System.out.print("[");\n'
        f"{_3}for (int i = 0; i < outputs.size(); i++) {{\n"
        f'{_4}if (i > 0) System.out.print(",");\n'
        f"{_4}System.out.print(outputs.get(i));\n"
        f"{_3}}}\n"
        f'{_3}System.out.println("]");\n'
        f'{_3}System.out.println("___CODERACER_TC_SEP___");\n'
        f"{_2}}}\n"
        f"{_1}}}\n"
        f"}}\n"
    )
    return runner_code


def _generate_java_code(
    methods, input_output_function, is_multi, class_name, constructor_method, block
):
    block += f"class {class_name} {{\n"
    if is_multi:
        if constructor_method:
            c_inputs = list(constructor_method.parameters.all().order_by("id"))
            c_args = ", ".join(
                f"{get_java_type(v.type, v.template_type, v.array_dimensions)} {v.name}"
                for v in c_inputs
            )
            block += f"{T}public {class_name}({c_args}) {{\n{T * 2}\n{T}}}\n\n"
        else:
            block += f"{T}public {class_name}() {{\n{T * 2}\n{T}}}\n\n"

    for method in methods:
        if method.is_constructor:
            continue
        inputs = list(method.parameters.all().order_by("id"))
        ret_type = get_java_type(
            method.type, method.template_type, method.array_dimensions
        )
        args = ", ".join(
            f"{get_java_type(v.type, v.template_type, v.array_dimensions)} {v.name}"
            for v in inputs
        )
        block += f"{T}public {ret_type} {method.name}({args}) {{\n{T * 2}// add your method calls here\n{T * 2}\n{T}}}\n"
    block += "}\n"

    if not is_multi and methods:
        method = methods[0]
        inputs = list(method.parameters.all().order_by("id"))
        ret_type = get_java_type(
            method.type, method.template_type, method.array_dimensions
        )
        _2 = T * 2
        _3 = T * 3
        runner_code = (
            f"public class Main {{\n"
            f"{generate_java_print_res(method.type, method.template_type, method.array_dimensions)}"
        )
        runner_code += (
            f"{T}public static void main(String[] args) {{\n"
            f"{_2}Scanner sc = new Scanner(System.in);\n"
            f"{_2}if (!sc.hasNextInt()) return;\n"
            f"{_2}int T = sc.nextInt();\n"
            f"{_2}for (int _tc = 0; _tc < T; _tc++) {{\n"
        )
        for v in inputs:
            if v.type == VariableType.ARRAY:
                runner_code += (
                    f"{_3}{get_java_type(v.type, v.template_type, v.array_dimensions)} {v.name};\n"
                    f"{generate_java_reader(v.name, v.template_type, v.array_dimensions, depth=3, is_root=True)}"
                )
            elif (
                v.type not in dict(VariableType.choices)
                and v.type != VariableType.ARRAY
            ):
                t = get_java_type(v.type)
                if input_output_function.strip():
                    runner_code += f"{_3}{t} {v.name} = Parser.input(sc);\n"
                else:
                    runner_code += (
                        f"{_3}{t} {v.name} = null; // TODO: Implement parsing logic\n"
                    )
            else:
                t_java = get_java_type(v.type, v.template_type, v.array_dimensions)
                if v.type == VariableType.INTEGER:
                    runner_code += f"{_3}{t_java} {v.name} = sc.nextInt();\n"
                elif v.type == VariableType.STRING:
                    runner_code += (
                        f'{_3}sc.skip("\\\\s*");\n'
                        f"{_3}{t_java} {v.name} = sc.nextLine();\n"
                    )
                elif v.type == VariableType.BOOLEAN:
                    runner_code += f"{_3}{t_java} {v.name} = sc.nextBoolean();\n"
                else:
                    runner_code += f"{_3}{t_java} {v.name} = sc.next();\n"

        call = f"sol.{method.name}({', '.join([v.name for v in inputs])})"
        runner_code += f"\n{_3}{class_name} sol = new {class_name}();\n"
        if (
            method.type != "void"
            and method.type != "VOID"
            and method.type
            and ret_type != "void"
        ):
            runner_code += (
                f'{_3}System.out.println("_USER_PRINT_START_");\n'
                f"{_3}long _t0 = System.nanoTime();\n"
                f"{_3}{ret_type} result = {call};\n"
                f"{_3}long _t1 = System.nanoTime();\n"
                f"{_3}long _tc_t_ns = _t1 - _t0;\n"
                f'{_3}System.out.println("_USER_PRINT_END_");\n'
                f'{_3}System.out.println("_TIME_" + _tc_t_ns + "_");\n'
            )
            if has_custom_print(input_output_function, method.type, "JAVA"):
                runner_code += f"{_3}Parser.print(result);\n{_3}System.out.println();\n"
            else:
                runner_code += (
                    f"{_3}_print_res(result);\n" f"{_3}System.out.println();\n"
                )
        else:
            runner_code += (
                f'{_3}System.out.println("_USER_PRINT_START_");\n'
                f"{_3}long _t0 = System.nanoTime();\n"
                f"{_3}{call};\n"
                f"{_3}long _t1 = System.nanoTime();\n"
                f"{_3}long _tc_t_ns = _t1 - _t0;\n"
                f'{_3}System.out.println("_USER_PRINT_END_");\n'
                f'{_3}System.out.println("_TIME_" + _tc_t_ns + "_");\n'
            )
        runner_code += (
            f'{_3}System.out.println("___CODERACER_TC_SEP___");\n'
            f"{_2}}}\n"
            f"{T}}}\n"
            f"}}\n"
        )
    elif is_multi:
        runner_code = _generate_java_multi_runner(
            methods, input_output_function, class_name, constructor_method
        )
    else:
        runner_code = "public class Main { public static void main(String[] args) {} }"

    return runner_code, block
