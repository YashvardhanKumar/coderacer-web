import pytest
from django.urls import reverse
from rest_framework import status
from .models import Problem, Tags, Difficulty


@pytest.mark.django_db
class TestProblemAPI:
    def test_list_problems(self, client):
        # Create a sample problem
        tag = Tags.objects.create(tags="Array")
        problem = Problem.objects.create(
            name="Two Sum",
            problem_description="Solve two sum",
            difficulty=Difficulty.EASY,
        )
        problem.tags.add(tag)

        url = reverse("problem-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check if the problem is in the results
        # Assuming PaginatedResponse based on viewset
        assert len(response.data["results"]) >= 1
        assert response.data["results"][0]["name"] == "Two Sum"

    def test_get_problem_detail(self, client):
        problem = Problem.objects.create(
            name="Unique Problem",
            problem_description="Detail check",
            difficulty=Difficulty.MEDIUM,
        )
        url = reverse("problem-detail", args=[problem.id])
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Unique Problem"

    def test_filter_by_tag(self, client):
        tag = Tags.objects.create(tags="Recursion")
        p1 = Problem.objects.create(name="Fibonacci", difficulty=Difficulty.EASY)
        p1.tags.add(tag)
        Problem.objects.create(name="Merge Sort", difficulty=Difficulty.MEDIUM)

        url = reverse("problem-by-tag")
        response = client.get(url, {"tag": "Recursion"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Fibonacci"


@pytest.mark.django_db
def test_generate_codeblocks_for_problem_force():
    from django.db.models.signals import post_save, post_delete
    from .signals import on_method_change, on_variable_change
    from .models import Problem, Method, Variable, Codeblock
    from .utils import generate_codeblocks_for_problem

    # Disconnect signals to test raw generation function isolation
    post_save.disconnect(on_method_change, sender=Method)
    post_save.disconnect(on_variable_change, sender=Variable)

    try:
        problem = Problem.objects.create(
            name="Add Two Numbers",
            problem_description="Add two numbers",
            difficulty=Difficulty.EASY,
        )
        method = Method.objects.create(
            problem=problem,
            name="add",
            type="INTEGER",
            array_dimensions=0,
        )
        Variable.objects.create(
            problem=problem,
            method=method,
            name="a",
            type="INTEGER",
            array_dimensions=0,
        )

        # Initial generation
        generate_codeblocks_for_problem(problem)
        assert problem.codeblocks.exists()
        cpp_cb = problem.codeblocks.get(language="CPP")
        initial_block = cpp_cb.block

        # Change the method name to "sum_values"
        method.name = "sum_values"
        method.save()

        # Generate without force: block should retain the old suffix (the "add" signature)
        generate_codeblocks_for_problem(problem, force=False)
        cpp_cb.refresh_from_db()
        assert "add(" in cpp_cb.block
        assert "sum_values(" not in cpp_cb.block

        # Generate with force=True: block should be updated to have "sum_values" signature
        generate_codeblocks_for_problem(problem, force=True)
        cpp_cb.refresh_from_db()
        assert "sum_values(" in cpp_cb.block
        assert "add(" not in cpp_cb.block
    finally:
        # Reconnect signals
        post_save.connect(on_method_change, sender=Method)
        post_save.connect(on_variable_change, sender=Variable)


@pytest.mark.django_db
def test_custom_type_parsing_and_printing():
    from .models import Problem, Method, Variable, CustomType, CustomTypeLanguage
    from .utils import generate_codeblocks_for_problem

    problem = Problem.objects.create(
        name="Custom Type Problem",
        problem_description="Check custom type features",
        difficulty=Difficulty.EASY,
    )
    # Method returns custom type ListNode and accepts ListNode
    method = Method.objects.create(
        problem=problem,
        name="solve",
        type="ListNode",
        array_dimensions=0,
    )
    Variable.objects.create(
        problem=problem,
        method=method,
        name="head",
        type="ListNode",
        array_dimensions=0,
    )

    # Set up CustomType and CustomTypeLanguage
    ct = CustomType.objects.create(name="ListNode")

    # C++ Custom Type Language with input and print
    CustomTypeLanguage.objects.create(
        custom_type=ct,
        language="CPP",
        class_declaration="struct ListNode { int val; ListNode* next; };",
        input_output_function="ListNode* input() { return nullptr; }\nvoid print(ListNode* head) { }",
    )

    # Java Custom Type Language with input and print
    CustomTypeLanguage.objects.create(
        custom_type=ct,
        language="JAVA",
        class_declaration="class ListNode { int val; ListNode next; }",
        input_output_function="class Parser {\n    static ListNode input(Scanner sc) { return null; }\n    static void print(ListNode head) {}\n}",
    )

    # Generate code blocks
    generate_codeblocks_for_problem(problem, force=True)

    # Check CPP
    from .utils import assemble_full_code

    cpp_cb = problem.codeblocks.get(language="CPP")

    # In database:
    assert "ListNode* head = input();" in cpp_cb.runner_code
    assert "print(result);" in cpp_cb.runner_code
    assert "struct ListNode" not in cpp_cb.runner_code
    assert "struct ListNode" in cpp_cb.block
    assert "ListNode* input()" not in cpp_cb.runner_code

    # Assembled for Judge0:
    cpp_assembled = assemble_full_code(problem, "CPP", "class Solution {};")
    assert "struct ListNode { int val; ListNode* next; };" in cpp_assembled
    assert "ListNode* input() { return nullptr; }" in cpp_assembled
    assert "class Solution {};" in cpp_assembled
    assert "ListNode* head = input();" in cpp_assembled

    # Check Java
    java_cb = problem.codeblocks.get(language="JAVA")

    # In database:
    assert "ListNode head = Parser.input(sc);" in java_cb.runner_code
    assert "Parser.print(result);" in java_cb.runner_code
    assert "class ListNode" not in java_cb.runner_code
    assert "class ListNode" in java_cb.block
    assert "class Parser" not in java_cb.runner_code

    # Assembled for Judge0:
    java_assembled = assemble_full_code(problem, "JAVA", "class Solution {}")
    assert "class ListNode { int val; ListNode next; }" in java_assembled
    assert "class Parser {" in java_assembled
    assert "class Solution {}" in java_assembled
    assert "ListNode head = Parser.input(sc);" in java_assembled


@pytest.mark.django_db(transaction=True)
def test_signals_auto_regenerate_codeblocks():
    from .models import Problem, Method, Variable, Codeblock
    from .utils import generate_codeblocks_for_problem

    problem = Problem.objects.create(
        name="Signal Test Problem",
        problem_description="Verify signals run",
        difficulty=Difficulty.EASY,
    )
    method = Method.objects.create(
        problem=problem,
        name="old_method_name",
        type="INTEGER",
        array_dimensions=0,
    )
    Variable.objects.create(
        problem=problem,
        method=method,
        name="a",
        type="INTEGER",
        array_dimensions=0,
    )

    # Initial generation (we trigger it manually once)
    generate_codeblocks_for_problem(problem)
    cpp_cb = problem.codeblocks.get(language="CPP")
    assert "old_method_name(" in cpp_cb.block

    # Update Method name and save: should trigger post_save signal and regenerate
    method.name = "new_method_name"
    method.save()

    cpp_cb.refresh_from_db()
    assert "new_method_name(" in cpp_cb.block
    assert "old_method_name(" not in cpp_cb.block


def test_clean_js_ts_fs_imports():
    from .utils import clean_js_ts_fs_imports
    from user.models import CodingLanguage

    js_code = "const fs = require('fs');\nconst data = fs.readFileSync(0);\nconsole.log(data);"
    cleaned_js = clean_js_ts_fs_imports(js_code, CodingLanguage.JAVASCRIPT)
    assert "const fs = require('fs');" not in cleaned_js
    assert "const data = fs.readFileSync(0);" in cleaned_js

    ts_code = "import * as fs from 'fs';\ndeclare var require: any;\nconst fs = require('fs');\nconst x = 42;"
    cleaned_ts = clean_js_ts_fs_imports(ts_code, CodingLanguage.TYPESCRIPT)
    assert "import * as fs from 'fs';" not in cleaned_ts
    assert "const fs = require('fs');" not in cleaned_ts
    assert "declare var require: any;" not in cleaned_ts
    assert "const x = 42;" in cleaned_ts


@pytest.mark.django_db
def test_multi_method_code_generation():
    from .models import Problem, Method, Variable
    from .utils import generate_codeblocks_for_problem
    from problem.models import Difficulty

    problem = Problem.objects.create(
        name="Browser History",
        problem_description="Simulate browser history",
        difficulty=Difficulty.MEDIUM,
    )
    # Constructor: BrowserHistory(string homepage)
    constructor = Method.objects.create(
        problem=problem,
        name="BrowserHistory",
        type="void",
        is_constructor=True,
        array_dimensions=0,
    )
    Variable.objects.create(
        problem=problem,
        method=constructor,
        name="homepage",
        type="STRING",
        array_dimensions=0,
    )

    # Method 1: void visit(string url)
    visit_method = Method.objects.create(
        problem=problem,
        name="visit",
        type="void",
        array_dimensions=0,
    )
    Variable.objects.create(
        problem=problem,
        method=visit_method,
        name="url",
        type="STRING",
        array_dimensions=0,
    )

    # Method 2: string back(int steps)
    back_method = Method.objects.create(
        problem=problem,
        name="back",
        type="STRING",
        array_dimensions=0,
    )
    Variable.objects.create(
        problem=problem,
        method=back_method,
        name="steps",
        type="INTEGER",
        array_dimensions=0,
    )

    # Generate code blocks
    generate_codeblocks_for_problem(problem, force=True)

    # Verify C++ block/runner
    cpp_cb = problem.codeblocks.get(language="CPP")
    assert "vector<string> outputs;" in cpp_cb.runner_code
    assert 'cout << "_USER_PRINT_START_"' in cpp_cb.runner_code
    assert 'cout << "_USER_PRINT_END_"' in cpp_cb.runner_code
    assert "outputs.push_back(ss.str());" in cpp_cb.runner_code
    assert 'outputs.push_back("null");' in cpp_cb.runner_code
    assert "delete obj" in cpp_cb.runner_code

    # Verify Python block/runner
    py_cb = problem.codeblocks.get(language="PYTHON")
    assert "outputs = []" in py_cb.runner_code
    assert "print('_USER_PRINT_START_')" in py_cb.runner_code
    assert "print('_USER_PRINT_END_')" in py_cb.runner_code
    assert "outputs.append(res)" in py_cb.runner_code
    assert "outputs.append(None)" in py_cb.runner_code

    # Verify JS block/runner
    js_cb = problem.codeblocks.get(language="JAVASCRIPT")
    assert "const outputs = [];" in js_cb.runner_code
    assert 'console.log("_USER_PRINT_START_");' in js_cb.runner_code
    assert 'console.log("_USER_PRINT_END_");' in js_cb.runner_code
    assert "outputs.push(res);" in js_cb.runner_code
    assert "outputs.push(null);" in js_cb.runner_code

    # Verify Java block/runner
    java_cb = problem.codeblocks.get(language="JAVA")
    assert "List<String> outputs = new ArrayList<>();" in java_cb.runner_code
    assert 'System.out.println("_USER_PRINT_START_");' in java_cb.runner_code
    assert 'System.out.println("_USER_PRINT_END_");' in java_cb.runner_code
    assert "outputs.add(baos.toString());" in java_cb.runner_code
    assert 'outputs.add("null");' in java_cb.runner_code


@pytest.mark.django_db
def test_generate_testcases_task_normalization(monkeypatch):
    from unittest.mock import MagicMock
    from ai.tasks import generate_testcases_task
    from ai.services import AIService
    from .models import Problem, Method, Variable, Codeblock, Testcase
    from problem.models import Difficulty

    # Create problem
    problem = Problem.objects.create(
        name="Browser History",
        problem_description="Simulate browser history",
        difficulty=Difficulty.MEDIUM,
    )
    # Mark it as is_multi by adding constructor and method
    constructor = Method.objects.create(
        problem=problem,
        name="BrowserHistory",
        type="void",
        is_constructor=True,
    )
    Variable.objects.create(
        problem=problem,
        method=constructor,
        name="homepage",
        type="STRING",
    )
    visit_method = Method.objects.create(
        problem=problem,
        name="visit",
        type="void",
    )
    Variable.objects.create(
        problem=problem,
        method=visit_method,
        name="url",
        type="STRING",
    )
    Codeblock.objects.create(
        problem=problem,
        language="CPP",
        block="class BrowserHistory {}",
    )

    from engine.models import TaskLog

    # Mock task request id
    generate_testcases_task.request.id = "test-task-123"

    # 1. Test is_multi structured inputs (input_methods + input_args)
    mock_response_1 = '[{"input_methods": ["BrowserHistory", "visit"], "input_args": [["homepage"], ["url"]], "output": [null, null]}]'
    mock_generate = MagicMock(return_value=(mock_response_1, "gemini"))
    monkeypatch.setattr(AIService, "generate_with_fallback", mock_generate)

    generate_testcases_task.run(problem.id, 1)

    tc = Testcase.objects.filter(problem=problem).first()
    assert tc is not None
    assert tc.input == '["BrowserHistory","visit"]\n[["homepage"],["url"]]'
    assert tc.output == "[null,null]"

    # Clean testcases
    Testcase.objects.all().delete()
    TaskLog.objects.all().delete()

    # 2. Test is_multi fallback: list of lists in "input"
    mock_response_2 = '[{"input": [["BrowserHistory", "visit"], [["homepage"], ["url"]]], "output": "[null, null]"}]'
    mock_generate.return_value = (mock_response_2, "gemini")

    # Set new request id
    generate_testcases_task.request.id = "test-task-456"
    generate_testcases_task.run(problem.id, 1)

    tc = Testcase.objects.filter(problem=problem).first()
    assert tc is not None
    assert tc.input == '["BrowserHistory","visit"]\n[["homepage"],["url"]]'
    assert tc.output == "[null,null]"

    # Clean testcases
    Testcase.objects.all().delete()
    TaskLog.objects.all().delete()

    # 3. Test is_multi fallback: string with single quotes and spaces
    mock_response_3 = "[{\"input\": \"['BrowserHistory', 'visit']\\n[['homepage'], ['url']]\", \"output\": \"[null, null]\"}]"
    mock_generate.return_value = (mock_response_3, "gemini")

    # Set new request id
    generate_testcases_task.request.id = "test-task-789"
    generate_testcases_task.run(problem.id, 1)

    tc = Testcase.objects.filter(problem=problem).first()
    assert tc is not None
    assert tc.input == '["BrowserHistory","visit"]\n[["homepage"],["url"]]'
    assert tc.output == "[null,null]"

    # Final cleanup for step 3
    Testcase.objects.all().delete()
    TaskLog.objects.all().delete()

    # 4. Test is_multi with solution_code included in prompt
    mock_response_4 = '[{"input_methods": ["BrowserHistory", "visit"], "input_args": [["homepage"], ["url"]], "output": [null, null]}]'
    mock_generate.return_value = (mock_response_4, "gemini")
    mock_generate.reset_mock()

    # Set new request id
    generate_testcases_task.request.id = "test-task-abc"
    generate_testcases_task.run(
        problem.id, 1, solution_code="class Solution { void visit() {} }"
    )

    tc = Testcase.objects.filter(problem=problem).first()
    assert tc is not None
    assert tc.input == '["BrowserHistory","visit"]\n[["homepage"],["url"]]'

    # Check that mock_generate was called with prompt containing the solution code
    called_prompt = mock_generate.call_args[0][0]
    assert "class Solution { void visit() {} }" in called_prompt
    assert "Reference / Correct Solution Code:" in called_prompt

    # Final cleanup
    Testcase.objects.all().delete()
    TaskLog.objects.all().delete()
