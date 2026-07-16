import os
import json
from celery import shared_task
from engine.models import TaskLog
from .services import AIService
from problem.models import Problem, Testcase, DataType


@shared_task(bind=True)
def generate_testcases_task(self, problem_id, count, solution_code=None):
    """
    Background task to generate test cases using AI, optionally guided by a reference solution.
    """
    task_log = TaskLog.objects.create(
        task_id=self.request.id,
        name=f"AI Testcase Generation - Problem #{problem_id}",
        status="PROCESSING",
    )

    try:
        problem = Problem.objects.get(id=problem_id)
        codeblock = problem.codeblocks.first()

        if not codeblock:
            task_log.status = "ERROR"
            task_log.add_log("No codeblock found.")
            return "Failed: No codeblock"

        task_log.add_log(f"Starting generation for problem: {problem.name}")

        batch_size = 50
        remaining = count
        all_testcases = []
        providers = ["gemini", "openai"]

        while remaining > 0:
            current_batch = min(batch_size, remaining)

            # Collect existing testcases to avoid duplicates
            existing_tc = Testcase.objects.filter(problem=problem).values_list(
                "input", flat=True
            )[:20]
            existing_tc_str = "\n".join(existing_tc) if existing_tc else "None"

            # Describe variables and methods
            def format_type(obj):
                base = obj.type
                if obj.type == "ARRAY":
                    dim_str = "[]" * obj.array_dimensions
                    base = f"{obj.template_type}{dim_str}"
                return base

            methods = list(problem.methods.all())
            constructor_method = next((m for m in methods if m.is_constructor), None)
            class_name = constructor_method.name if constructor_method else "Solution"
            is_multi = len(methods) > 1 or any(m.is_constructor for m in methods)

            methods_list = []
            if is_multi and not constructor_method:
                # Add default constructor
                methods_list.append(
                    f"- Method: {class_name} | Return Type: void (Constructor - MUST be called first as the first command, takes no arguments)"
                )

            for m in methods:
                type_str = format_type(m)
                suffix = (
                    " (Constructor - MUST be called first as the first command)"
                    if m.is_constructor
                    else ""
                )
                methods_list.append(
                    f"- Method: {m.name} | Return Type: {type_str}{suffix}"
                )

            methods_str = "\n".join(methods_list)

            vars_str = "\n".join(
                [
                    f"- Variable: {v.name} | Type: {format_type(v)} | Target Method: {v.method.name if v.method else 'None'}"
                    for v in problem.variables.all()
                ]
            )

            if is_multi:
                format_requirements = """FORMAT REQUIREMENTS FOR TEST CASES:
            - Each testcase object in the JSON array MUST have the following structure:
              {
                "input_methods": ["Graph","shortestPath","addEdge","shortestPath"],
                "input_args": [[4,[[0,2,5],[0,1,2],[1,2,1],[3,0,3]]],[3,2],[[1,3,4]],[0,3]],
                "output": [null,6,null,6]
              }
            - Alternatively, you can use the "input" field but it MUST contain exactly two lines:
              1. A raw JSON array of strings containing the sequence of method calls (e.g., ["Graph","shortestPath"]).
              2. A raw JSON array of arrays containing the list of arguments passed to each call (e.g., [[4,[[0,2,5]]],[3,2]]).
            - "input_methods" MUST be a JSON array of strings containing the sequence of method/function calls, starting with the constructor class name or initial method.
            - "input_args" MUST be a JSON array of arrays containing the list of arguments passed to each corresponding method/function call.
            - "output" MUST be a JSON array representing the return value of each function call, in order (use null for constructor calls or methods returning void/None).
            - There MUST NOT be any spaces after commas inside any arrays/lists (e.g., generate '[1,2]' instead of '[1, 2]'). This applies to all fields."""
            else:
                format_requirements = """FORMAT REQUIREMENTS FOR 'input' AND 'output' FIELDS:
            - The 'input' field MUST ONLY contain the values of the variables, each written on a new line, in order.
            - Do NOT include any variable names, assignments, or labels (e.g., do NOT generate 'nums = [1,5,9,2,8]', instead generate '[1,5,9,2,8]').
            - Any array or list (including nested arrays/matrices) MUST be enclosed in square brackets '[]' (e.g., '[1,5,9,2,8]' or '[[1,2],[3,4]]').
            - There MUST NOT be any spaces after commas inside any arrays/lists (e.g., generate '[1,5,9,2,8]' instead of '[1, 5, 9, 2, 8]', and '[[1,2],[3,4]]' instead of '[[1, 2], [3, 4]]'). This applies to both the 'input' and 'output' fields."""

            prompt_format = (
                '[ {"input_methods": [...], "input_args": [...], "output": [...]}, ... ]'
                if is_multi
                else '[ {"input": "...", "output": "..."}, ... ]'
            )
            solution_str = ""
            if solution_code:
                solution_str = f"""
            Reference / Correct Solution Code:
            {solution_code}

            Use the logic of this reference solution code to generate correct outputs for the testcases.
            """
            prompt = f"""
            You are an expert competitive programmer. Generate exactly {current_batch} unique test cases for the following problem.

            Problem Description:
            {problem.problem_description}

            Methods:
            {methods_str}

            Variables (Inputs):
            {vars_str}

            Code Template:
            {codeblock.block}
            {solution_str}
            # Dry run the generated testcases using the reference solution code to produce expected outputs. Also use the example of an existing testcase as a pattern when generating new ones.

            Existing Testcases (do not duplicate these):
            {existing_tc_str}

            {format_requirements}

            Output MUST be a raw JSON array of objects.
            Format: {prompt_format}
            """

            used_provider = None
            try:
                content, used_provider = AIService.generate_with_fallback(
                    prompt, providers
                )
                task_log.add_log(
                    f"Requesting batch of {current_batch} from {used_provider}..."
                )
                print(content)  # Debug log

                content = AIService.clean_json_string(content)
                batch_data = json.loads(content)

                if isinstance(batch_data, list) and len(batch_data) > 0:
                    task_log.add_log(
                        f"Successfully parsed {len(batch_data)} test cases from {used_provider}."
                    )
                    for data in batch_data:
                        input_str = ""
                        output_str = ""

                        if is_multi:
                            # 1. Try to get input_methods and input_args
                            methods_val = (
                                data.get("input_methods")
                                or data.get("methods")
                                or data.get("calls")
                            )
                            args_val = (
                                data.get("input_args")
                                or data.get("arguments")
                                or data.get("args")
                            )

                            # If they are not present, try to extract from "input"
                            if not methods_val or not args_val:
                                raw_in = data.get("input", "")
                                if isinstance(raw_in, list):
                                    if (
                                        len(raw_in) == 2
                                        and isinstance(raw_in[0], list)
                                        and isinstance(raw_in[1], list)
                                    ):
                                        methods_val = raw_in[0]
                                        args_val = raw_in[1]
                                    elif len(raw_in) > 0 and all(
                                        isinstance(x, str) for x in raw_in
                                    ):
                                        methods_val = raw_in
                                elif isinstance(raw_in, str):
                                    lines = [
                                        line.strip()
                                        for line in raw_in.strip().splitlines()
                                        if line.strip()
                                    ]
                                    if len(lines) == 2:
                                        try:
                                            methods_val = json.loads(lines[0])
                                            args_val = json.loads(lines[1])
                                        except Exception:
                                            pass
                                    elif len(lines) == 1:
                                        try:
                                            parsed_in = json.loads(lines[0])
                                            if (
                                                isinstance(parsed_in, list)
                                                and len(parsed_in) == 2
                                                and isinstance(parsed_in[0], list)
                                                and isinstance(parsed_in[1], list)
                                            ):
                                                methods_val = parsed_in[0]
                                                args_val = parsed_in[1]
                                        except Exception:
                                            pass

                            # Normalize parsed types
                            if isinstance(methods_val, str):
                                try:
                                    methods_val = json.loads(methods_val)
                                except Exception:
                                    pass
                            if isinstance(args_val, str):
                                try:
                                    args_val = json.loads(args_val)
                                except Exception:
                                    pass

                            if isinstance(methods_val, list) and isinstance(
                                args_val, list
                            ):
                                methods_str_val = json.dumps(
                                    methods_val, separators=(",", ":")
                                )
                                args_str_val = json.dumps(
                                    args_val, separators=(",", ":")
                                )
                                input_str = f"{methods_str_val}\n{args_str_val}"
                            else:
                                raw_in = data.get("input", "")
                                if isinstance(raw_in, list):
                                    input_str = json.dumps(
                                        raw_in, separators=(",", ":")
                                    )
                                else:
                                    input_str = str(raw_in).replace(" ", "")

                            output_val = data.get("output", "")
                            if isinstance(output_val, list):
                                output_str = json.dumps(
                                    output_val, separators=(",", ":")
                                )
                            elif isinstance(output_val, str):
                                try:
                                    parsed_out = json.loads(output_val)
                                    if isinstance(parsed_out, list):
                                        output_str = json.dumps(
                                            parsed_out, separators=(",", ":")
                                        )
                                    else:
                                        output_str = output_val.replace(" ", "")
                                except Exception:
                                    output_str = output_val.replace(" ", "")
                            else:
                                output_str = str(output_val).replace(" ", "")

                        else:
                            # is_multi is False
                            raw_in = data.get("input", "")
                            if isinstance(raw_in, list):
                                lines_normalized = []
                                for item in raw_in:
                                    if isinstance(item, (list, dict)):
                                        lines_normalized.append(
                                            json.dumps(item, separators=(",", ":"))
                                        )
                                    else:
                                        lines_normalized.append(str(item))
                                input_str = "\n".join(lines_normalized)
                            elif isinstance(raw_in, str):
                                lines = raw_in.strip().splitlines()
                                lines_normalized = []
                                for line in lines:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    if "=" in line:
                                        line = line.split("=", 1)[1].strip()
                                    try:
                                        parsed = json.loads(line)
                                        if isinstance(parsed, (list, dict)):
                                            lines_normalized.append(
                                                json.dumps(
                                                    parsed, separators=(",", ":")
                                                )
                                            )
                                            continue
                                    except Exception:
                                        pass
                                    lines_normalized.append(line.replace(" ", ""))
                                input_str = "\n".join(lines_normalized)
                            else:
                                input_str = str(raw_in)

                            output_val = data.get("output", "")
                            if isinstance(output_val, (list, dict)):
                                output_str = json.dumps(
                                    output_val, separators=(",", ":")
                                )
                            elif isinstance(output_val, str):
                                try:
                                    parsed = json.loads(output_val)
                                    if isinstance(parsed, (list, dict)):
                                        output_str = json.dumps(
                                            parsed, separators=(",", ":")
                                        )
                                    else:
                                        output_str = output_val.replace(" ", "")
                                except Exception:
                                    output_str = output_val.replace(" ", "")
                            else:
                                output_str = str(output_val).replace(" ", "")

                        # Double check formatting quotes & spaces
                        if (
                            input_str.startswith("['")
                            or ",'" in input_str
                            or "'," in input_str
                        ):
                            input_str = input_str.replace("'", '"')
                        if (
                            output_str.startswith("['")
                            or ",'" in output_str
                            or "'," in output_str
                        ):
                            output_str = output_str.replace("'", '"')

                        all_testcases.append(
                            Testcase(
                                problem=problem,
                                input=input_str,
                                output=output_str,
                                display_testcase=False,
                            )
                        )
                    remaining -= len(batch_data)
                    percent = int(((count - remaining) / count) * 100)
                    task_log.progress = percent
                    task_log.save()
                else:
                    task_log.add_log(
                        f"{used_provider} returned invalid format. Retrying..."
                    )

            except Exception as e:
                task_log.add_log(f"Batch Error: {str(e)}")
                # We can choose to fail or continue. Let's try once more or fail if fatal.
                if used_provider is None:
                    raise e  # Fatal if all providers failed in generate_with_fallback
                if "429" in str(e) and used_provider in ("openai", "ChatGPT"):
                    raise e  # Fatal if OpenAI also fails

        if all_testcases:
            task_log.add_log(f"Saving {len(all_testcases)} test cases to database...")
            Testcase.objects.bulk_create(all_testcases)
            task_log.add_log("Database sync complete.")

        task_log.status = "SUCCESS"
        task_log.progress = 100
        task_log.save()
        return f"Successfully generated {len(all_testcases)} test cases."

    except Exception as e:
        task_log.status = "ERROR"
        task_log.add_log(f"FATAL ERROR: {str(e)}")
        task_log.save()
        return f"Failed: {str(e)}"
