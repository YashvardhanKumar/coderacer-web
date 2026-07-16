import re
from problem.models import VariableType
from problem.shared_utils import has_custom_print

T = "    "


def get_ts_type(var_type, template_type=None, dimensions=1):
    mapping = {
        VariableType.INTEGER: "number",
        VariableType.STRING: "string",
        VariableType.BOOLEAN: "boolean",
        VariableType.CHAR: "string",
        VariableType.FLOAT: "number",
        VariableType.LONG: "number",
    }
    if var_type == VariableType.ARRAY:
        inner = get_ts_type(template_type)
        if " | null" in inner:
            inner = f"({inner})"
        return f"{inner}{'[]' * dimensions}"
    if var_type not in mapping and var_type and var_type not in ["void", "VOID"]:
        return f"{var_type} | null"
    return mapping.get(var_type, "any")


def clean_js_ts_fs_imports(code, language):
    if not code:
        return code
    from user.models import CodingLanguage

    if language == CodingLanguage.JAVASCRIPT:
        code = re.sub(r"const\s+fs\s*=\s*require\(['\"]fs['\"]\);?", "", code)
    elif language == CodingLanguage.TYPESCRIPT:
        for p in [
            r"const\s+fs\s*=\s*require\(['\"]fs['\"]\);?",
            r"import\s+(\*\s+as\s+)?fs\s+from\s+['\"]fs['\"];?",
            r"import\s+fs\s*=\s*require\(['\"]fs['\"]\);?",
            r"declare\s+var\s+require\s*:\s*any;?",
        ]:
            code = re.sub(p, "", code)
    return code


def generate_js_ts_print_res(ret_type, template_type, dimensions):
    if ret_type in ["void", "VOID"]:
        return ""
    is_array = ret_type == VariableType.ARRAY or ret_type == "Array"

    code = (
        "function _print_res(val) {\n"
        f"{T}if (val === null || val === undefined) {{\n"
        f"{T}    console.log('null');\n"
        f"{T}    return;\n"
        f"{T}}}\n"
    )

    if not is_array:
        if ret_type == VariableType.BOOLEAN:
            code += f'{T}console.log(val ? "true" : "false");\n'
        else:
            code += f"{T}console.log(val);\n"
    elif dimensions == 1 and template_type == VariableType.STRING:
        code += (
            f"{T}for(let i = 0; i < val.length; i++) {{\n"
            f"{T}    console.log(val[i] !== null ? val[i] : 'null');\n"
            f"{T}}}\n"
        )
    else:
        code += _generate_js_ts_print_array(template_type, dimensions, "val", 1)
    code += "}\n\n"
    return code


def _generate_js_ts_print_array(template_type, dimensions, var_name, depth):
    indent = T * depth
    loop_var = f"i{dimensions}"
    if dimensions == 1:
        if template_type == VariableType.BOOLEAN:
            return f'{indent}console.log({var_name}.map(x => x === null ? "null" : (x ? "true" : "false")).join(" "));\n'
        else:
            return f"{indent}console.log({var_name}.map(x => x === null ? 'null' : x).join(\" \"));\n"

    code = (
        f"{indent}for(let {loop_var} = 0; {loop_var} < {var_name}.length; {loop_var}++) {{\n"
        f"{T * (depth + 1)}if ({var_name}[{loop_var}] === null) {{ console.log('null'); }} else {{\n"
        f"{_generate_js_ts_print_array(template_type, dimensions - 1, f'{var_name}[{loop_var}]', depth + 2)}"
        f"{T * (depth + 1)}}}\n"
        f"{indent}}}\n"
    )
    return code


def _generate_js_ts_multi_runner(lang_name, methods, class_name, constructor_method):
    """Build the JS/TS runner for multi-method / constructor problems."""
    _2 = T * 2
    _3 = T * 3
    _4 = T * 4
    runner_code = ""
    if lang_name == "TYPESCRIPT":
        runner_code += "declare var require: any;\n"
    runner_code += (
        f"\nconst input_data = fs.readFileSync(0, 'utf-8').trim().split('\\n');\n"
        f"if (input_data.length > 0) {{\n"
        f"{T}const T = parseInt(input_data[0].trim());\n"
        f"{T}let idx = 1;\n"
        f"{T}for (let _tc = 0; _tc < T; _tc++) {{\n"
        f"{_2}const commands = JSON.parse(input_data[idx++].trim());\n"
        f"{_2}const args_list = JSON.parse(input_data[idx++].trim());\n"
        f"{_2}const outputs = [];\n"
        f"{_2}let obj = null;\n"
        f'{_2}console.log("_USER_PRINT_START_");\n'
        f"{_2}let _total_t_ns = 0;\n"
        f"{_2}for(let i=0; i<commands.length; i++) {{\n"
        f"{_3}const cmd = commands[i];\n"
        f"{_3}const args = args_list[i];\n"
    )

    if constructor_method:
        runner_code += (
            f"{_3}if (cmd === '{class_name}') {{\n"
            f"{_4}obj = new {class_name}(...args);\n"
            f"{_4}outputs.push(null);\n"
            f"{_3}}}\n"
        )
    else:
        runner_code += (
            f"{_3}if (cmd === '{class_name}') {{\n"
            f"{_4}obj = new {class_name}();\n"
            f"{_4}outputs.push(null);\n"
            f"{_3}}}\n"
        )

    for method in methods:
        if method.is_constructor:
            continue
        runner_code += f"{_3}else if (cmd === '{method.name}') {{\n"
        runner_code += f"{_4}const _ts = process.hrtime.bigint();\n"
        if method.type != "void" and method.type != "VOID" and method.type:
            runner_code += (
                f"{_4}const res = obj.{method.name}(...args);\n"
                f"{_4}outputs.push(res);\n"
            )
        else:
            runner_code += (
                f"{_4}obj.{method.name}(...args);\n" f"{_4}outputs.push(null);\n"
            )
        runner_code += f"{_4}const _te = process.hrtime.bigint();\n"
        runner_code += f"{_4}_total_t_ns += Number(_te - _ts);\n"
        runner_code += f"{_3}}}\n"

    runner_code += (
        f"{_2}}}\n"
        f'{_2}console.log("_USER_PRINT_END_");\n'
        f"{_2}const _tc_t_ns = _total_t_ns;\n"
        f"{_2}console.log(`_TIME_${{_tc_t_ns}}_`);\n"
        f"{_2}console.log(JSON.stringify(outputs));\n"
        f'{_2}console.log("___CODERACER_TC_SEP___");\n'
        f"{T}}}\n"
        f"}}\n"
    )
    return runner_code


def _generate_js_ts_code(
    lang_name,
    methods,
    input_output_function,
    is_multi,
    class_name,
    constructor_method,
    block,
):
    block += f"class {class_name} {{\n"
    if is_multi:
        if constructor_method:
            c_inputs = list(constructor_method.parameters.all().order_by("id"))
            if lang_name == "TYPESCRIPT":
                c_args = ", ".join(
                    f"{v.name}: {get_ts_type(v.type, v.template_type, v.array_dimensions)}"
                    for v in c_inputs
                )
            else:
                c_args = ", ".join([v.name for v in c_inputs])
            block += f"{T}constructor({c_args}) {{\n{T * 2}\n{T}}}\n\n"
        else:
            block += f"{T}constructor() {{\n{T * 2}\n{T}}}\n\n"

    for method in methods:
        if method.is_constructor:
            continue
        inputs = list(method.parameters.all().order_by("id"))
        if lang_name == "TYPESCRIPT":
            ret_type = f": {get_ts_type(method.type, method.template_type, method.array_dimensions)}"
            args = ", ".join(
                f"{v.name}: {get_ts_type(v.type, v.template_type, v.array_dimensions)}"
                for v in inputs
            )
        else:
            ret_type = ""
            args = ", ".join([v.name for v in inputs])
            jsdoc = f"{T}/**\n"
            for v in inputs:
                t = (
                    get_ts_type(v.type, v.template_type, v.array_dimensions)
                    .replace(" | null", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                jsdoc += f"     * @param {{{t}}} {v.name}\n"
            ret_t = (
                get_ts_type(method.type, method.template_type, method.array_dimensions)
                .replace(" | null", "")
                .replace("(", "")
                .replace(")", "")
            )
            if method.type not in ["void", "VOID"] and method.type:
                jsdoc += f"     * @return {{{ret_t}}}\n"
            jsdoc += "     */\n"
            block += jsdoc

        block += f"{T}{method.name}({args}){ret_type} {{\n{T * 2}// add your method calls here\n{T * 2}\n{T}}}\n"
    block += "}\n"

    if not is_multi and methods:
        method = methods[0]
        inputs = list(method.parameters.all().order_by("id"))
        runner_code = ""
        if lang_name == "TYPESCRIPT":
            runner_code += "declare var require: any;\n"
        runner_code += generate_js_ts_print_res(
            method.type, method.template_type, method.array_dimensions
        )
        _2 = T * 2
        runner_code += (
            f"const input_data = fs.readFileSync(0, 'utf-8').trim().split('\\n');\n"
            f"if (input_data.length > 0) {{\n"
            f"{T}const T = parseInt(input_data[0].trim());\n"
            f"{T}let idx = 1;\n"
            f"{T}for (let _tc = 0; _tc < T; _tc++) {{\n"
        )
        for v in inputs:
            if (
                v.type not in dict(VariableType.choices)
                and v.type != VariableType.ARRAY
            ):
                if input_output_function.strip():
                    runner_code += f"{_2}const {v.name} = input(input_data[idx++]);\n"
                else:
                    runner_code += f"{_2}const {v.name} = null; idx++; // TODO: Implement parsing logic for custom type {v.type}\n"
            else:
                runner_code += (
                    f"{_2}const {v.name} = JSON.parse(input_data[idx++].trim());\n"
                )

        call = f"solution.{method.name}({', '.join([v.name for v in inputs])})"
        runner_code += f"{_2}const solution = new {class_name}();\n"
        if method.type != "void" and method.type != "VOID" and method.type:
            runner_code += (
                f'{_2}console.log("_USER_PRINT_START_");\n'
                f"{_2}const _t0 = process.hrtime.bigint();\n"
                f"{_2}const result = {call};\n"
                f"{_2}const _t1 = process.hrtime.bigint();\n"
                f"{_2}const _tc_t_ns = Number(_t1 - _t0);\n"
                f'{_2}console.log("_USER_PRINT_END_");\n'
                f"{_2}console.log(`_TIME_${{_tc_t_ns}}_`);\n"
            )
            if has_custom_print(input_output_function, method.type, lang_name):
                runner_code += f"{_2}print(result);\n"
            else:
                runner_code += f"{_2}_print_res(result);\n"
        else:
            runner_code += (
                f'{_2}console.log("_USER_PRINT_START_");\n'
                f"{_2}const _t0 = process.hrtime.bigint();\n"
                f"{_2}{call};\n"
                f"{_2}const _t1 = process.hrtime.bigint();\n"
                f"{_2}const _tc_t_ns = Number(_t1 - _t0);\n"
                f'{_2}console.log("_USER_PRINT_END_");\n'
                f"{_2}console.log(`_TIME_${{_tc_t_ns}}_`);\n"
            )
        runner_code += (
            f'{_2}console.log("___CODERACER_TC_SEP___");\n' f"{T}}}\n" f"}}\n"
        )
    elif is_multi:
        runner_code = _generate_js_ts_multi_runner(
            lang_name, methods, class_name, constructor_method
        )
    else:
        runner_code = ""
        if lang_name == "TYPESCRIPT":
            runner_code += "declare var require: any;\n"

    return runner_code, block
