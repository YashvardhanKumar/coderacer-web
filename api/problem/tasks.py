from celery import shared_task
from .models import Problem
from .utils import generate_codeblocks_for_problem


@shared_task
def generate_codeblocks_task(problem_id, force=True):
    try:
        problem = Problem.objects.get(id=problem_id)
        generate_codeblocks_for_problem(problem, force=force)
    except Problem.DoesNotExist:
        pass


@shared_task(bind=True)
def generate_testcases_programmatic_task(
    self,
    problem_id,
    generator_code,
    generator_language,
    solution_code,
    solution_language,
    count,
):
    import time
    import requests
    import json
    import re
    from engine.models import TaskLog
    from .models import Problem, Testcase
    from .utils import assemble_full_code
    from engine.services import encode_base64, decode_base64
    from engine.constants import JUDGE0_URL

    task_log = TaskLog.objects.create(
        task_id=self.request.id,
        name=f"Programmatic Testcase Generation - Problem #{problem_id}",
        status="PROCESSING",
    )

    try:
        problem = Problem.objects.get(id=problem_id)
        task_log.add_log(
            f"Starting programmatic generation for problem: {problem.name}"
        )

        generator_lang_id = 71 if generator_language == "PYTHON" else 54
        solution_lang_id = 71 if solution_language == "PYTHON" else 54

        task_log.add_log(
            f"Generator Language: {generator_language} (ID: {generator_lang_id})"
        )
        task_log.add_log(
            f"Solution Language: {solution_language} (ID: {solution_lang_id})"
        )
        code_preview = solution_code[:120].replace("\n", "\\n")
        task_log.add_log(f"Solution code (first 120 chars): {code_preview}")
        GEN_BATCH_SIZE = 15
        BATCH_SIZE = 15
        from engine.constants import TC_SEPARATOR, get_scaled_limits

        cleaned_gen = re.sub(
            r'if\s+__name__\s*==\s*["\']__main__["\']\s*:.*',
            "",
            generator_code,
            flags=re.DOTALL,
        ).strip()

        import random as _seed_rng

        master_seed = _seed_rng.random()
        seeds = _seed_rng.Random(master_seed).choices(range(1, 10**9 + 1), k=count)

        inputs = []
        for gen_start in range(1, count + 1, GEN_BATCH_SIZE):
            gen_end = min(gen_start + GEN_BATCH_SIZE - 1, count)
            gen_n = gen_end - gen_start + 1
            task_log.add_log(
                f"Generator batch {gen_start}-{gen_end} ({gen_n} test cases)..."
            )

            seed_array = ", ".join(
                str(seeds[i - 1]) for i in range(gen_start, gen_end + 1)
            )
            wrapped = f"""import sys, io
{cleaned_gen}

if __name__ == "__main__":
    _seeds = [{seed_array}]
    for idx in range({gen_n}):
        sys.stdin = io.StringIO(str(_seeds[idx]))
        generate()
        if idx < {gen_n} - 1:
            print("{TC_SEPARATOR}")
"""

            resp = requests.post(
                f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=true",
                json={
                    "source_code": encode_base64(wrapped),
                    "language_id": generator_lang_id,
                    **get_scaled_limits(1),
                },
                timeout=120,
            )

            if resp.status_code != 200:
                raise Exception(
                    f"Generator batch submission failed: {resp.status_code} {resp.text[:500]}"
                )

            gen_res = resp.json()

            if "token" in gen_res and "status" not in gen_res:
                token = gen_res["token"]
                task_log.add_log(f"Judge0 returned token. Polling...")
                for attempt in range(60):
                    time.sleep(2)
                    poll = requests.get(
                        f"{JUDGE0_URL}/submissions/{token}?base64_encoded=true&fields=status,stdout,stderr,compile_output,message",
                        timeout=30,
                    )
                    if poll.status_code == 200:
                        gen_res = poll.json()
                        status_obj = gen_res.get("status") or {}
                        status_id = (
                            status_obj.get("id")
                            if isinstance(status_obj, dict)
                            else None
                        )
                        if status_id not in (1, 2):
                            break
                else:
                    raise Exception(f"Timed out polling generator batch {gen_start}.")

            for field in ["stdout", "stderr", "compile_output"]:
                val = gen_res.get(field)
                if val is not None:
                    try:
                        gen_res[field] = decode_base64(val)
                    except Exception:
                        pass

            status_obj = gen_res.get("status") or {}
            status_id = status_obj.get("id") if isinstance(status_obj, dict) else None
            status_desc = (
                status_obj.get("description", "unknown")
                if isinstance(status_obj, dict)
                else str(status_obj)
            )
            task_log.add_log(
                f"Generator batch Judge0 status: {status_id} ({status_desc})"
            )

            if status_id not in (3,):
                compile_out = gen_res.get("compile_output", "")
                stderr = gen_res.get("stderr", "")
                err_msg = f"Generator batch failed with status '{status_desc}'."
                if compile_out:
                    err_msg += f"\nCompile Output:\n{compile_out}"
                if stderr:
                    err_msg += f"\nStderr:\n{stderr}"
                raise Exception(err_msg)

            raw_stdout = gen_res.get("stdout", "").strip()
            if not raw_stdout:
                raise Exception("Generator batch produced no output.")

            from engine.services import parse_batch_stdout

            batch_inputs = parse_batch_stdout(raw_stdout, gen_n)
            inputs.extend(inp for inp in batch_inputs if inp.strip())
            task_log.add_log(
                f"  Got {sum(1 for i in batch_inputs if i.strip())} inputs from this batch."
            )

        task_log.add_log(f"Generated {len(inputs)} total inputs from generator.")

        task_log.add_log(
            f"Successfully generated {len(inputs)} inputs. Running reference solution in batches of {BATCH_SIZE}..."
        )
        task_log.progress = 50
        task_log.save()

        from engine.services import (
            parse_batch_stdout,
            format_batch_stdin,
            reconstruct_json_output,
        )
        from engine.constants import get_scaled_limits

        full_code = assemble_full_code(problem, solution_language, solution_code)
        all_actual_outputs = {}

        for batch_start in range(0, len(inputs), BATCH_SIZE):
            batch_inputs = inputs[batch_start : batch_start + BATCH_SIZE]
            batch_end = min(batch_start + BATCH_SIZE, len(inputs))
            task_log.add_log(
                f"Submitting batch {batch_start // BATCH_SIZE + 1} ({batch_start+1}-{batch_end})..."
            )

            fake_testcases = [
                {"input": inp, "problem_id": problem.id} for inp in batch_inputs
            ]
            batch_stdin = format_batch_stdin(fake_testcases, solution_lang_id)
            scaled_limits = get_scaled_limits(len(batch_inputs))
            payload = {
                "source_code": encode_base64(full_code),
                "language_id": solution_lang_id,
                "stdin": encode_base64(batch_stdin),
                **scaled_limits,
            }

            resp = requests.post(
                f"{JUDGE0_URL}/submissions?base64_encoded=true&wait=true",
                json=payload,
                timeout=120,
            )

            try:
                res = resp.json()
            except Exception as e:
                raise Exception(
                    f"Failed to parse Judge0 response: {e}. Body: {resp.text[:500]}"
                )

            if "token" in res and "status" not in res:
                token = res["token"]
                task_log.add_log(f"Judge0 returned token. Polling...")
                for attempt in range(60):
                    time.sleep(2)
                    poll_resp = requests.get(
                        f"{JUDGE0_URL}/submissions/{token}?base64_encoded=true&fields=status,stdout,stderr,compile_output,message",
                        timeout=30,
                    )
                    if poll_resp.status_code == 200:
                        res = poll_resp.json()
                        status_obj = res.get("status") or {}
                        status_id = (
                            status_obj.get("id")
                            if isinstance(status_obj, dict)
                            else None
                        )
                        if status_id not in (1, 2):
                            break
                else:
                    raise Exception(
                        f"Timed out polling batch {batch_start // BATCH_SIZE + 1}."
                    )

            for field in ["stdout", "stderr", "compile_output", "message"]:
                val = res.get(field)
                if val is not None:
                    try:
                        res[field] = decode_base64(val)
                    except Exception:
                        pass

            status_obj = res.get("status") or {}
            status_id = status_obj.get("id") if isinstance(status_obj, dict) else None
            status_desc = (
                status_obj.get("description", "unknown")
                if isinstance(status_obj, dict)
                else str(status_obj)
            )
            task_log.add_log(
                f"Batch {batch_start // BATCH_SIZE + 1} Judge0 status: {status_id} ({status_desc})"
            )

            if status_id == 6:
                raise Exception(f"Compilation Error:\n{res.get('compile_output', '')}")
            if status_id in (5, 7, 8, 9, 10, 11, 12, 13, 14):
                raise Exception(
                    f"Reference solution failed: {status_desc}\nStderr:\n{res.get('stderr', '')}"
                )

            raw_stdout = res.get("stdout", "")
            batch_outputs = parse_batch_stdout(raw_stdout, len(batch_inputs))
            for bidx, out in enumerate(batch_outputs):
                all_actual_outputs[batch_start + bidx] = out

        task_log.progress = 85
        task_log.save()

        all_testcases = []
        for idx, raw_input in enumerate(inputs):
            block_text = all_actual_outputs.get(idx, "")
            if not block_text:
                continue
            # Strip _TIME_ markers inserted by runner
            time_marker_match = re.search(r"_TIME_(\d+)_", block_text)
            if time_marker_match:
                block_text = re.sub(r"_TIME_\d+_[\r\n]*", "", block_text)

            pattern = r"_USER_PRINT_START_[\r\n]*(.*?)[\r\n]*_USER_PRINT_END_[\r\n]*"
            cleaned = re.sub(pattern, "", block_text, flags=re.DOTALL).strip("\n\r")
            cleaned = (
                cleaned.replace("_USER_PRINT_START_", "")
                .replace("_USER_PRINT_END_", "")
                .strip("\n\r")
            )
            cleaned = reconstruct_json_output(cleaned, problem)
            all_testcases.append(
                Testcase(
                    problem=problem,
                    input=raw_input,
                    output=cleaned if cleaned else "",
                    display_testcase=False,
                )
            )

        if all_testcases:
            task_log.add_log(f"Saving {len(all_testcases)} test cases to database...")
            Testcase.objects.bulk_create(all_testcases)
            task_log.add_log("Database sync complete.")
        else:
            task_log.add_log(
                "Warning: No test cases were created — the solution code produced no output. "
                "Make sure to paste a working solution (the auto-populated scaffold is a stub)."
            )

        task_log.status = "SUCCESS"
        task_log.progress = 100
        task_log.save()
        return f"Successfully generated {len(all_testcases)} test cases."

    except Exception as e:
        task_log.status = "ERROR"
        task_log.add_log(f"FATAL ERROR: {str(e)}")
        task_log.save()
        return f"Failed: {str(e)}"
