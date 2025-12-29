# submissions/services.py
import requests
from .constants import JUDGE0_URL, DEFAULT_LIMITS
from problem.models import Problem, Testcase, AnswerStatus
from engine.constants import parse_input, parse_output
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q


def submit_to_judge0(payload: dict, is_submit: bool) -> dict:
    merged_payload = {
        **DEFAULT_LIMITS,
        **payload,
    }
    pid = merged_payload.get('problem_id')
    
    if is_submit:
        testcases = Testcase.objects.filter(problem_id=pid, display_testcase=True)
    else:
        testcases = Testcase.objects.filter(problem_id=pid)
        
    responses = []
    for tc in testcases:
        print(tc.output)
        merged_payload['expected_output'] = parse_output(tc.output)
        merged_payload['stdin'] = parse_input(tc.input)
        response = requests.post(
            url=f'{JUDGE0_URL}/submissions/?fields=*&wait=true',
            json=merged_payload,
            headers={"Content-Type": "application/json"}
        )
        responses.append(response)

                #  "X-Auth-Token": os.getenv("AUTHN_TOKEN", ""),
                #  "X-Auth-User": os.getenv("AUTHZ_TOKEN", "")
    
    results = []
    
    for response in responses:
        response.raise_for_status()
        res = response.json()
        if is_submit:
            if res["status"]["description"] != AnswerStatus.AC:
                return {**res, **(res["status"])}
        else:
            results.append(res)
    if is_submit:
        return {"status": AnswerStatus.AC, "description": "All testcases passed"}
    return results