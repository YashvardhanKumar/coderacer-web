from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Problem, Codeblock, Testcase, DataType
from django import forms
import json
import os
from django.contrib import messages
from django.contrib import admin
from django.contrib.auth import get_user_model, login
from django.http import StreamingHttpResponse, JsonResponse
from django.forms import inlineformset_factory
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from user.models import CodingLanguage
from ai.services import AIService
from ai.tasks import generate_testcases_task

User = get_user_model()


@staff_member_required
def rootops(request):
    return render(
        request,
        "problem/rootops.html",
        {
            "user": request.user,
            "is_superuser": request.user.is_superuser,
            "languages": [
                (lang_code, lang_name)
                for lang_code, lang_name in CodingLanguage.choices
            ],
        },
    )


def root_login(request):
    return redirect("moderator_login")


class ModeratorLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "custom-input", "placeholder": "Enter moderator email"}
        )
    )


def moderator_login(request):
    if request.method == "POST":
        form = ModeratorLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email, is_staff=True).first()
            if user:
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )
                messages.success(request, f"Logged in as moderator: {user.username}")
                return redirect("rootops")
            else:
                messages.error(request, "No moderator found with this email.")
    else:
        form = ModeratorLoginForm()
    return render(request, "admin/moderator_login.html", {"form": form})


class CustomProblemForm(forms.ModelForm):
    problem_description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Problem
        fields = [
            "name",
            "problem_description",
            "difficulty",
            "validator_type",
            "custom_validator",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "custom-input", "placeholder": "Problem Title"}
            ),
            "difficulty": forms.Select(attrs={"class": "custom-input"}),
            "validator_type": forms.Select(attrs={"class": "custom-input"}),
            "custom_validator": forms.Textarea(
                attrs={
                    "class": "custom-input",
                    "placeholder": "def validate(actual, expected, tc_input):\n    # Return True if correct, False otherwise\n    return actual.strip() == expected.strip()",
                    "rows": 6,
                }
            ),
        }

    class Media:
        js = ("admin/js/codeblock_updater.js", "admin/js/cm6_loader.js")


CodeBlockFormSet = inlineformset_factory(
    Problem,
    Codeblock,
    fields=["language", "block", "runner_code"],
    extra=0,
    can_delete=True,
    widgets={
        "language": forms.Select(attrs={"class": "custom-input"}),
        "block": forms.Textarea(
            attrs={
                "class": "custom-input",
                "rows": 10,
                "placeholder": "Boilerplate code for the user",
            }
        ),
        "runner_code": forms.Textarea(
            attrs={
                "class": "custom-input",
                "rows": 10,
                "placeholder": "Runner code for execution",
            }
        ),
    },
)

from .models import Variable, Method


class TypeSelectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import VariableType, CustomType

        choices = list(VariableType.choices)
        custom_types = CustomType.objects.all()
        for ct in custom_types:
            choices.append((ct.name, f"Custom: {ct.name}"))

        type_choices = [("", "---------")] + choices

        if "type" in self.fields:
            old_field = self.fields["type"]
            self.fields["type"] = forms.ChoiceField(
                label=old_field.label,
                help_text=old_field.help_text,
                choices=type_choices,
                widget=forms.Select(attrs={"class": "custom-input"}),
            )
        if "template_type" in self.fields:
            old_field = self.fields["template_type"]
            temp_choices = [("", "---------")] + choices
            self.fields["template_type"] = forms.ChoiceField(
                label=old_field.label,
                help_text=old_field.help_text,
                choices=temp_choices,
                required=False,
                widget=forms.Select(attrs={"class": "custom-input"}),
            )


MethodFormSet = inlineformset_factory(
    Problem,
    Method,
    form=TypeSelectForm,
    fields=["name", "is_constructor", "type", "template_type", "array_dimensions"],
    extra=1,
    can_delete=True,
    widgets={
        "name": forms.TextInput(
            attrs={"class": "custom-input", "placeholder": "Method Name"}
        ),
        "is_constructor": forms.CheckboxInput(
            attrs={"style": "margin-left: 10px; transform: scale(1.2);"}
        ),
        "array_dimensions": forms.NumberInput(
            attrs={"class": "custom-input", "min": 1}
        ),
    },
)

VariableFormSet = inlineformset_factory(
    Problem,
    Variable,
    form=TypeSelectForm,
    fields=["method", "name", "type", "template_type", "array_dimensions"],
    extra=1,
    can_delete=True,
    widgets={
        "method": forms.Select(attrs={"class": "custom-input"}),
        "name": forms.TextInput(
            attrs={"class": "custom-input", "placeholder": "Variable Name"}
        ),
        "array_dimensions": forms.NumberInput(
            attrs={"class": "custom-input", "min": 1}
        ),
    },
)

from .models import ProblemTags

ProblemTagsFormSet = inlineformset_factory(
    Problem,
    ProblemTags,
    fields=["tag"],
    extra=1,
    can_delete=True,
    widgets={
        "tag": forms.Select(attrs={"class": "custom-input"}),
    },
)


class CustomTypeForm(forms.ModelForm):
    class Meta:
        from .models import CustomType

        model = CustomType
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "custom-input", "placeholder": "e.g., ListNode"}
            )
        }


from .models import CustomType, CustomTypeLanguage

CustomTypeLanguageFormSet = inlineformset_factory(
    CustomType,
    CustomTypeLanguage,
    fields=["language", "class_declaration", "input_output_function"],
    extra=1,
    can_delete=True,
    widgets={
        "language": forms.Select(attrs={"class": "custom-input"}),
        "class_declaration": forms.Textarea(attrs={"class": "custom-input", "rows": 4}),
        "input_output_function": forms.Textarea(
            attrs={"class": "custom-input", "rows": 4}
        ),
    },
)


class CustomTestcaseForm(forms.ModelForm):
    class Meta:
        model = Testcase
        fields = ["problem", "input", "output", "display_testcase"]
        widgets = {
            "problem": forms.Select(attrs={"class": "custom-input"}),
            "input": forms.Textarea(
                attrs={
                    "class": "custom-input",
                    "rows": 3,
                    "placeholder": "Test input...",
                }
            ),
            "output": forms.Textarea(
                attrs={
                    "class": "custom-input",
                    "rows": 3,
                    "placeholder": "Expected output...",
                }
            ),
            "display_testcase": forms.CheckboxInput(attrs={"class": "custom-checkbox"}),
        }


@staff_member_required
def generate_testcases_async(request):
    """
    Starts a background task to generate test cases.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    problem_id = request.POST.get("problem")
    count = int(request.POST.get("count", 100))
    solution_code = request.POST.get("solution_code", "")

    # Start Celery task
    task = generate_testcases_task.delay(problem_id, count, solution_code)

    return JsonResponse({"status": "pending", "task_id": task.id})


import json
from .utils import generate_code_for_language
from user.models import CodingLanguage
from django.views.decorators.csrf import csrf_exempt


@staff_member_required
@csrf_exempt
def generate_codeblocks_preview(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        variables_data = data.get("variables", [])
        object_declarations = data.get("object_declarations", {})
        input_functions = data.get(
            "input_output_functions", data.get("input_functions", {})
        )

        # We need to construct mock variable objects
        class MockVariable:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        class MockManager:
            def __init__(self, items=None):
                self.items = items or []

            def all(self):
                return self

            def order_by(self, *args):
                return self.items

        class MockMethod:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
                self.parameters = MockManager()

        variables = []
        for v in variables_data:
            if not v.get("name") or not v.get("type"):
                continue
            variables.append(
                MockVariable(
                    name=v.get("name"),
                    type=v.get("type"),
                    custom_type_name=v.get("custom_type_name", ""),
                    template_type=v.get("template_type", ""),
                    array_dimensions=int(v.get("array_dimensions") or 1),
                )
            )

        if not variables:
            return JsonResponse({"error": "No variables defined"}, status=400)

        dummy_method = MockMethod(name="solve", type="void", array_dimensions=1)
        dummy_method.parameters.items = variables

        results = {}
        for lang_code, lang_name in CodingLanguage.choices:
            obj_decl = object_declarations.get(lang_code, "")
            inp_func = input_functions.get(lang_code, "")
            runner_code, block = generate_code_for_language(
                lang_code, [dummy_method], obj_decl, inp_func
            )
            results[lang_code] = {"runner_code": runner_code, "block": block}

        return JsonResponse({"success": True, "codeblocks": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def add_problem_custom(request):
    step = int(request.GET.get("step", 1))
    problem_id = request.GET.get("problem_id")
    loading = request.GET.get("loading") == "1"
    problem = None
    if problem_id:
        from django.shortcuts import get_object_or_404
        from .models import Problem

        problem = get_object_or_404(Problem, id=problem_id)

    form = CustomProblemForm(instance=problem)
    tags_formset = ProblemTagsFormSet(instance=problem)

    ct_form = CustomTypeForm()
    ctl_formset = CustomTypeLanguageFormSet()

    method_formset = MethodFormSet(instance=problem)
    var_formset = VariableFormSet(instance=problem)
    formset = CodeBlockFormSet(instance=problem)

    if request.method == "POST":
        post_data = request.POST.copy()
        if step == 1:
            form = CustomProblemForm(post_data, instance=problem)
            if form.is_valid():
                problem = form.save()
                return redirect(
                    f"/api/rootops/add-problem/?step=2&problem_id={problem.id}"
                )
        elif step == 2:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")
            tags_formset = ProblemTagsFormSet(post_data, instance=problem)
            if tags_formset.is_valid():
                tags_formset.save()

                new_tags_str = post_data.get("new_tags", "")
                if new_tags_str:
                    from .models import Tags, ProblemTags

                    tag_names = [
                        t.strip() for t in new_tags_str.split(",") if t.strip()
                    ]
                    for t_name in tag_names:
                        tag, created = Tags.objects.get_or_create(tags=t_name)
                        ProblemTags.objects.get_or_create(problem=problem, tag=tag)

                return redirect(
                    f"/api/rootops/add-problem/?step=3&problem_id={problem.id}"
                )
        elif step == 3:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")

            if "skip" in post_data:
                return redirect(
                    f"/api/rootops/add-problem/?step=4&problem_id={problem.id}"
                )

            ct_form = CustomTypeForm(post_data)
            if ct_form.is_valid():
                ct = ct_form.save()
                ctl_formset = CustomTypeLanguageFormSet(post_data, instance=ct)
                if ctl_formset.is_valid():
                    ctl_formset.save()
                    return redirect(
                        f"/api/rootops/add-problem/?step=4&problem_id={problem.id}"
                    )
        elif step == 4:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")
            method_formset = MethodFormSet(post_data, instance=problem)
            if method_formset.is_valid():
                method_formset.save()

                # Automatically create a constructor method if there are multiple methods
                # and no constructor method has been defined yet.
                non_constructor_methods = problem.methods.filter(is_constructor=False)
                has_constructor = problem.methods.filter(is_constructor=True).exists()
                if non_constructor_methods.count() > 1 and not has_constructor:
                    Method.objects.create(
                        problem=problem,
                        name="Solution",
                        type="void",
                        is_constructor=True,
                        array_dimensions=0,
                    )

                return redirect(
                    f"/api/rootops/add-problem/?step=5&problem_id={problem.id}"
                )
        elif step == 5:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")
            var_formset = VariableFormSet(post_data, instance=problem)
            # Ensure method queryset is correct for validation
            for f in var_formset.forms:
                if "method" in f.fields:
                    f.fields["method"].queryset = problem.methods.all()
            if var_formset.is_valid():
                var_formset.save()
                from .tasks import generate_codeblocks_task

                generate_codeblocks_task.delay(problem.id, force=True)
                return redirect(
                    f"/api/rootops/add-problem/?step=5&loading=1&problem_id={problem.id}"
                )
        elif step == 6:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")
            formset = CodeBlockFormSet(post_data, instance=problem)
            if formset.is_valid():
                formset.save()
                messages.success(
                    request,
                    f"Problem '{problem.name}' created successfully with its methods, variables, and code blocks! Now add some test cases.",
                )
                return redirect(
                    f"/api/rootops/add-problem/?step=7&problem_id={problem.id}"
                )
        elif step == 7:
            if not problem:
                return redirect("/api/rootops/add-problem/?step=1")

            # Step 6 allows submitting either a manual testcase or starting AI generation
            if "add_manual" in post_data:
                manual_form = CustomTestcaseForm(post_data)
                if manual_form.is_valid():
                    tc = manual_form.save(commit=False)
                    tc.problem = problem
                    tc.save()
                    messages.success(request, "Manual testcase added successfully!")
                else:
                    messages.error(request, "Failed to add manual testcase.")
            elif "generate_ai" in post_data:
                ai_form = AITestCaseForm(post_data)
                if ai_form.is_valid():
                    count = ai_form.cleaned_data["count"]
                    solution_code = ai_form.cleaned_data.get("solution_code", "")
                    from ai.tasks import generate_testcases_task

                    task = generate_testcases_task.delay(
                        problem.id, count, solution_code
                    )
                    messages.success(
                        request,
                        f"AI generation started for {count} testcases. Task ID: {task.id}",
                    )
                else:
                    messages.error(request, "Invalid AI testcase parameters.")
            elif "finish" in post_data:
                return redirect("admin:problem_problem_change", problem.id)

            return redirect(f"/api/rootops/add-problem/?step=7&problem_id={problem.id}")

    # GET or invalid POST handling
    if step == 5 and problem:
        for f in var_formset.forms:
            if "method" in f.fields:
                f.fields["method"].queryset = problem.methods.all()

    if step == 6 and problem and request.method == "GET":
        from .utils import generate_codeblocks_for_problem

        if not problem.codeblocks.exists():
            generate_codeblocks_for_problem(problem)
            formset = CodeBlockFormSet(instance=problem)

    manual_form = None
    ai_form = None
    prog_form = None
    if step == 7 and problem:
        manual_form = CustomTestcaseForm(initial={"problem": problem})
        # AI Form defaults to 10 count. We can set problem initial here too
        ai_form = AITestCaseForm(initial={"problem": problem, "count": 10})
        prog_form = ProgrammaticTestCaseForm(initial={"problem": problem, "count": 20})

    empty_var_form = var_formset.empty_form
    if problem:
        if "method" in empty_var_form.fields:
            empty_var_form.fields["method"].queryset = problem.methods.all()
        for f in var_formset.forms:
            if "method" in f.fields:
                f.fields["method"].queryset = problem.methods.all()

    return render(
        request,
        "problem/add_problem_custom.html",
        {
            "step": step,
            "problem": problem,
            "form": form,
            "tags_formset": tags_formset,
            "ct_form": ct_form,
            "ctl_formset": ctl_formset,
            "method_formset": method_formset,
            "var_formset": var_formset,
            "empty_var_form": empty_var_form,
            "formset": formset,
            "manual_form": manual_form,
            "ai_form": ai_form,
            "prog_form": prog_form,
            "languages": CodingLanguage.choices,
            "loading": loading,
        },
    )


@staff_member_required
def add_testcase_custom(request):
    manual_form = CustomTestcaseForm()
    ai_form = AITestCaseForm()
    prog_form = ProgrammaticTestCaseForm()

    if request.method == "POST":
        manual_form = CustomTestcaseForm(request.POST)
        if manual_form.is_valid():
            testcase = manual_form.save()
            messages.success(
                request, f"Testcase for '{testcase.problem.name}' added successfully!"
            )
            return redirect("admin:problem_testcase_changelist")

    return render(
        request,
        "problem/add_testcase_custom.html",
        {
            "form": manual_form,
            "ai_form": ai_form,
            "prog_form": prog_form,
        },
    )


class AITestCaseForm(forms.Form):
    problem = forms.ModelChoiceField(
        queryset=Problem.objects.all(), label="Select Problem"
    )
    count = forms.IntegerField(
        min_value=1, max_value=200, initial=100, label="Number of Test Cases"
    )
    solution_code = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "custom-input",
                "rows": 8,
                "placeholder": "Paste reference solution here...",
            }
        ),
        required=False,
        label="Solution Code (Optional)",
    )


@staff_member_required
def add_ai_testcases(request):
    if request.method == "POST":
        form = AITestCaseForm(request.POST)
        if form.is_valid():
            problem = form.cleaned_data["problem"]
            count = form.cleaned_data["count"]
            messages.info(request, "Starting AI generation process...")
            return redirect("add_testcase_custom")
    else:
        form = AITestCaseForm()
    return render(request, "problem/add_ai_testcases.html", {"form": form})


@staff_member_required
def check_codeblocks_status(request):
    problem_id = request.GET.get("problem_id")
    if not problem_id:
        return JsonResponse({"ready": False, "count": 0})
    from .models import Problem

    try:
        problem = Problem.objects.get(id=problem_id)
        count = problem.codeblocks.count()
        from user.models import CodingLanguage

        total_languages = len(CodingLanguage.choices)
        return JsonResponse(
            {
                "ready": count >= total_languages,
                "count": count,
                "total": total_languages,
            }
        )
    except Problem.DoesNotExist:
        return JsonResponse({"ready": False, "count": 0})


class ProgrammaticTestCaseForm(forms.Form):
    problem = forms.ModelChoiceField(
        queryset=Problem.objects.all(), label="Select Problem"
    )
    generator_language = forms.ChoiceField(
        choices=[("PYTHON", "Python")],
        initial="PYTHON",
        label="Generator Language",
        widget=forms.Select(attrs={"class": "custom-input"}),
    )
    generator_code = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "custom-input code-editor",
                "rows": 10,
                "placeholder": (
                    "Write generator code...\n"
                    "It should read the seed from stdin (e.g. cin >> seed; or seed = int(input())) and print a single testcase input to stdout."
                ),
            }
        ),
        label="Generator Code",
    )
    solution_language = forms.ChoiceField(
        choices=[("CPP", "C++"), ("PYTHON", "Python")],
        initial="CPP",
        label="Reference Solution Language",
        widget=forms.Select(attrs={"class": "custom-input"}),
    )
    solution_code = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "custom-input code-editor",
                "rows": 10,
                "placeholder": "Write reference solution code (Solution class/method)...",
            }
        ),
        label="Reference Solution Code",
    )
    count = forms.IntegerField(
        min_value=1, max_value=100, initial=20, label="Number of Test Cases"
    )


def build_generator_code(problem):
    """Generate a Python generator template based on problem's variable types."""
    import random as _r

    variables = problem.variables.select_related("method").order_by("method", "id")
    if not variables:
        return """import random
import json
import sys

def generate():
    seed = int(sys.stdin.readline().strip())
    rng = random.Random(seed)
    # TODO: define test case generation logic
    print("1")

if __name__ == "__main__":
    generate()
"""
    is_multi = getattr(problem, "is_multi", False)
    if is_multi:
        methods = list(problem.methods.all())
        constructor = next(
            (m for m in methods if m.is_constructor), methods[0] if methods else None
        )
        non_constructor = [m for m in methods if m != constructor]

        def gen_var_code(method, indent="    "):
            method_vars = [v for v in variables if v.method_id == method.id]
            var_lines = []
            for v in method_vars:
                var_lines.append(f"{indent}# {v.name}: TODO set correct range")
                if v.type == "INTEGER":
                    var_lines.append(f"{indent}{v.name} = rng.randint(1, 100)")
                elif v.type == "FLOAT":
                    var_lines.append(
                        f"{indent}{v.name} = round(rng.uniform(0.0, 100.0), 2)"
                    )
                elif v.type == "BOOLEAN":
                    var_lines.append(f"{indent}{v.name} = rng.randint(0, 1) == 1")
                elif v.type == "STRING":
                    var_lines.append(
                        f'{indent}{v.name} = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 10)))'
                    )
                elif v.type == "ARRAY":
                    var_lines.append(
                        f"{indent}{v.name} = [rng.randint(1, 100) for _ in range(rng.randint(1, 10))]"
                    )
                else:
                    var_lines.append(
                        f"{indent}{v.name} = None  # TODO: generate {v.type} value"
                    )
            return var_lines

        constr_vars_code = gen_var_code(constructor) if constructor else []
        constr_vars_names = [
            v.name
            for v in variables
            if v.method_id == (constructor.id if constructor else None)
        ]

        # Build per-method variable generation
        method_blocks = []
        if constructor:
            constr_args = ", ".join(constr_vars_names)
            method_blocks.append(f"    # Constructor: {constructor.name}")
            method_blocks.extend(constr_vars_code)
            method_blocks.append(f'    methods = ["{constructor.name}"]')
            method_blocks.append(f"    args = [[{constr_args}]]")
        else:
            method_blocks.append("    methods = []")
            method_blocks.append("    args = []")

        method_blocks.append("")
        if non_constructor:
            method_blocks.append("    # Random non-constructor calls")
            method_blocks.append(f"    num_calls = rng.randint(1, 5)")
            choices_str = ", ".join(f'"{m.name}"' for m in non_constructor)
            method_blocks.append(f"    for _ in range(num_calls):")
            method_blocks.append(f"        method_choice = rng.choice([{choices_str}])")
            for i, m in enumerate(non_constructor):
                method_name = m.name
                m_vars = [v for v in variables if v.method_id == m.id]
                m_var_names = [v.name for v in m_vars]
                m_var_names_str = ", ".join(m_var_names)
                m_var_code = gen_var_code(m, indent="            ")
                keyword = "if" if i == 0 else "elif"
                method_blocks.append(
                    f'        {keyword} method_choice == "{method_name}":'
                )
                method_blocks.append(f"            # {method_name}")
                method_blocks.extend(m_var_code)
                method_blocks.append(f'            methods.append("{method_name}")')
                method_blocks.append(f"            args.append([{m_var_names_str}])")

        method_code = "\n".join(method_blocks)

        return f"""import random
import json
import sys
import string

def generate():
    seed = int(sys.stdin.readline().strip())
    rng = random.Random(seed)
{method_code}
    print(json.dumps(methods))
    print(json.dumps(args))

if __name__ == "__main__":
    generate()
"""

    lines = [
        "import random",
        "import json",
        "import sys",
        "import string",
        "",
        "def generate():",
        "    seed = int(sys.stdin.readline().strip())",
        "    rng = random.Random(seed)",
        "",
        "    # Generate values for each variable in order",
    ]

    # Generate value and print-line for each variable
    for var in variables:
        name = var.name
        raw_type = var.type or "INTEGER"
        var_type_upper = raw_type.upper()
        ttype = (var.template_type or "").upper()
        dims = var.array_dimensions or 1

        from problem.models import VariableType as _VT, CustomType as _CT

        _std_types = {v.value.upper() for v in _VT}

        lines.append("    # {name}: {type}".format(name=name, type=raw_type))

        if var_type_upper in ("INTEGER", "LONG"):
            lines.append("    {name} = rng.randint(-1000, 1000)".format(name=name))
            lines.append("    print({name})".format(name=name))
        elif var_type_upper == "FLOAT":
            lines.append(
                "    {name} = round(rng.uniform(-1000.0, 1000.0), 2)".format(name=name)
            )
            lines.append("    print({name})".format(name=name))
        elif var_type_upper == "BOOLEAN":
            lines.append("    {name} = rng.choice([True, False])".format(name=name))
            lines.append("    print('true' if {name} else 'false')".format(name=name))
        elif var_type_upper == "CHAR":
            lines.append(
                "    {name} = rng.choice(string.ascii_letters)".format(name=name)
            )
            lines.append("    print({name})".format(name=name))
        elif var_type_upper == "STRING":
            lines.append(
                "    {name} = ''.join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 20)))".format(
                    name=name
                )
            )
            lines.append("    print(json.dumps({name}))".format(name=name))
        elif var_type_upper == "ARRAY":
            _inner = ttype if ttype else "INTEGER"
            _inner_upper = _inner.upper()
            if dims == 1:
                if _inner_upper in ("INTEGER", "LONG"):
                    _elem = "rng.randint(-100, 100)"
                elif _inner_upper == "FLOAT":
                    _elem = "round(rng.uniform(-100.0, 100.0), 2)"
                elif _inner_upper == "BOOLEAN":
                    _elem = "rng.choice([True, False])"
                elif _inner_upper == "CHAR":
                    _elem = "rng.choice(string.ascii_letters)"
                elif _inner_upper == "STRING":
                    _elem = "''.join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 10)))"
                else:
                    _elem = "rng.randint(-100, 100)"
                lines.append("    n = rng.randint(1, 10)")
                lines.append(
                    "    {name} = [{elem} for _ in range(n)]".format(
                        name=name, elem=_elem
                    )
                )
                lines.append("    print(json.dumps({name}))".format(name=name))
            else:
                lines.append(
                    "    {name} = [[rng.randint(-100, 100) for _ in range(rng.randint(1, 5))] for __ in range(rng.randint(1, 5))]".format(
                        name=name
                    )
                )
                lines.append("    print(json.dumps({name}))".format(name=name))
        elif var_type_upper == "OBJECT":
            lines.append(
                "    # TODO: generate object data matching problem's object structure"
            )
            lines.append(
                "    {name} = {{'key': rng.randint(1, 100)}}".format(name=name)
            )
            lines.append("    print(json.dumps({name}))".format(name=name))
        elif var_type_upper == "VOID":
            lines.append("    # VOID type — nothing to generate")
            lines.append("    print('null')")
        elif var_type_upper in _std_types:
            # Other standard types (CUSTOM selector, etc.)
            lines.append(
                "    # TODO: CUSTOM type generation for {name}".format(name=name)
            )
            lines.append("    {name} = None".format(name=name))
            lines.append(
                "    print(json.dumps({name}) if {name} is not None else 'null')".format(
                    name=name
                )
            )
        else:
            # Custom type name (e.g. ListNode, TreeNode) — look up input format
            _input_func = ""
            try:
                _ct_obj = _CT.objects.get(name=raw_type)
                from problem.models import CustomTypeLanguage as _CTL

                _py_entry = _ct_obj.languages.filter(language="PYTHON").first()
                if _py_entry and _py_entry.input_output_function:
                    _input_func = _py_entry.input_output_function
            except _CT.DoesNotExist:
                pass

            if _input_func:
                lines.append("    # Input format for {type}:".format(type=raw_type))
                for _ln in _input_func.strip().split("\n"):
                    lines.append("    #   {ln}".format(ln=_ln))
            lines.append(
                "    # TODO: generate {name} data matching the format above".format(
                    name=name
                )
            )
            lines.append("    {name} = None".format(name=name))
            lines.append(
                "    print(json.dumps({name}) if {name} is not None else 'null')".format(
                    name=name
                )
            )

    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    generate()")

    return "\n".join(lines) + "\n"


def get_problem_scaffolds(request):
    problem_id = request.GET.get("problem_id")
    if not problem_id:
        return JsonResponse({"error": "Missing problem_id"}, status=400)
    try:
        problem = Problem.objects.get(id=problem_id)
        from problem.models import Codeblock
        from user.models import CodingLanguage

        def get_solution_code(language, placeholder):
            cb = Codeblock.objects.filter(problem=problem, language=language).first()
            return cb.block.strip() if cb and cb.block else placeholder

        cpp_scaffold = get_solution_code(
            CodingLanguage.CPP, "// YOUR REFERENCE SOLUTION CLASS/METHOD HERE"
        )
        python_scaffold = get_solution_code(
            CodingLanguage.PYTHON, "# YOUR REFERENCE SOLUTION CLASS/METHOD HERE"
        )
        generator_code = (
            problem.generator_code.strip() if problem.generator_code else ""
        )
        if not generator_code:
            generator_code = build_generator_code(problem)

        return JsonResponse(
            {
                "CPP": cpp_scaffold,
                "PYTHON": python_scaffold,
                "generator_code": generator_code,
                "saved_generator": bool(problem.generator_code),
            }
        )
    except Problem.DoesNotExist:
        return JsonResponse({"error": "Problem not found"}, status=404)


def generate_generator_code_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    problem_id = request.POST.get("problem_id")
    if not problem_id:
        return JsonResponse({"error": "Missing problem_id"}, status=400)

    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        return JsonResponse({"error": "Problem not found"}, status=404)

    # Build method/variable description
    methods = list(problem.methods.all())
    methods_str = "\n".join(
        f"- Method: {m.name} | Return Type: {m.type}" for m in methods
    )

    from problem.models import VariableType, CustomType, CustomTypeLanguage

    variables = problem.variables.select_related("method").order_by("method", "id")
    vars_str_lines = []
    custom_type_names = set()
    for v in variables:
        line = f"- Variable: {v.name} | Type: {v.type}"
        if v.template_type:
            line += f"<{v.template_type}>"
        if v.type == "ARRAY":
            line += f"[] (dim={v.array_dimensions})"
        if v.method:
            line += f" | Method param of: {v.method.name}"
        vars_str_lines.append(line)

        # Track custom type names
        raw_type = v.type or ""
        if (
            raw_type.upper() not in {vt.value.upper() for vt in VariableType}
            and raw_type != "ARRAY"
        ):
            custom_type_names.add(raw_type)
        if v.template_type and v.template_type.upper() not in {
            vt.value.upper() for vt in VariableType
        }:
            custom_type_names.add(v.template_type)
    vars_str = "\n".join(vars_str_lines)

    # Gather custom type class declarations for the prompt
    custom_type_decls = []
    if custom_type_names:
        ctl_qs = CustomTypeLanguage.objects.filter(
            custom_type__name__in=custom_type_names, language="PYTHON"
        ).select_related("custom_type")
        for ctl in ctl_qs:
            if ctl.class_declaration:
                custom_type_decls.append(
                    f"Custom type '{ctl.custom_type.name}' Python class:\n{ctl.class_declaration}"
                )
    custom_types_section = ""
    if custom_type_decls:
        custom_types_section = (
            "\n\nCustom Type Python Classes:\n" + "\n\n".join(custom_type_decls) + "\n"
        )

    is_multi = len(methods) > 1 or any(m.is_constructor for m in methods)

    if is_multi:
        constructor = next((m for m in methods if m.is_constructor), None)
        constructor_name = constructor.name if constructor else methods[0].name
        prompt = f"""You are an expert competitive programmer. Generate a Python test case generator for the following multi-method problem.

Problem Description:
{problem.problem_description}

Methods:
{methods_str}

Variables (Input):
{vars_str}
{custom_types_section}
RULES:
- The generator reads an integer seed from stdin: seed = int(sys.stdin.readline().strip())
- Create a random.Random(seed) instance for reproducibility
- Generate ONE test case per invocation (each invocation gets a different seed)
- The test case is TWO LINES of JSON:
  Line 1: A JSON array of method names in invocation order
  Line 2: A JSON array of argument arrays, one per method call
- The constructor ("{constructor_name}") MUST be first, called exactly once
- After the constructor, call 1–5 additional non-constructor methods in a realistic sequence
- Each method's arguments must match the variable types listed above
- The generated test cases MUST be valid — e.g., for BrowserHistory, ensure back/forward steps don't exceed history bounds
- Read the Constraints section from the Problem Description above. Every variable value must respect those constraints (e.g., if n is constrained 2 ≤ n ≤ 10⁴, generate n within that range)
- For strings with specific allowed characters in the constraints: if the constraint says a variable "consists of" symbols without listing specific ones, only include these default symbols: , - . ; ' " ! ?. If specific symbols are explicitly listed (e.g., '+', '-', '.'), then include ONLY the listed ones. chars = string.ascii_letters + string.digits + " ,-.;'\\\"!?"; s = "".join(rng.choices(chars, k=rng.randint(0, 200))). If symbols include backslash, double-quote, [, or ] in the allowed set, escape them with a backslash in the Python string so they don't break the string literal or the formatted input (which uses [ ] and ").
- For arrays, use json.dumps()
- For custom type objects, convert them to the expected input format
- For plain integers/strings/floats, pass them directly
- Do NOT add unnecessary comments. Only add a single-line comment above each variable showing the variable range (e.g., # n: 2 to 10)
- Output NO explanations, NO markdown — ONLY the Python code. The code must have a generate() function and an if __name__ == "__main__": block.

Example for BrowserHistory (constructor: BrowserHistory(homepage: string), methods: visit(url: string), back(steps: int), forward(steps: int)):
```python
import random
import json
import sys
import string

def generate():
    seed = int(sys.stdin.readline().strip())
    rng = random.Random(seed)
    homepage = "".join(rng.choices(string.ascii_lowercase) for _ in range(rng.randint(1, 10)))
    methods = ["BrowserHistory"]
    args = [[homepage]]
    num_calls = rng.randint(1, 5)
    for _ in range(num_calls):
        choice = rng.random()
        if choice < 0.5:
            url = "".join(rng.choices(string.ascii_lowercase) for _ in range(rng.randint(1, 10)))
            methods.append("visit")
            args.append([url])
        elif choice < 0.75:
            steps = rng.randint(1, 3)
            methods.append("back")
            args.append([steps])
        else:
            steps = rng.randint(1, 3)
            methods.append("forward")
            args.append([steps])
    print(json.dumps(methods))
    print(json.dumps(args))

if __name__ == "__main__":
    generate()
```"""
    else:
        prompt = f"""You are an expert competitive programmer. Generate a Python test case generator for the following problem.

Problem Description:
{problem.problem_description}

Methods:
{methods_str}

Variables (Input):
{vars_str}
{custom_types_section}
RULES:
- The generator reads an integer seed from stdin: seed = int(sys.stdin.readline().strip())
- Create a random.Random(seed) instance for reproducibility
- Generate ONE test case per invocation (each invocation gets a different seed)
- The generated test cases MUST be valid — e.g., for Two Sum, ensure the target is the sum of two distinct array elements; for linked list problems, ensure the list is properly constructed
- Print each variable value on its own line, in the order listed in Variables
- Read the Constraints section from the Problem Description above. Every variable value must respect those constraints (e.g., if n is constrained 2 ≤ n ≤ 10⁴, generate n within that range)
- For strings with specific allowed characters in the constraints: if the constraint says a variable "consists of" symbols without listing specific ones, only include these default symbols: , - . ; ' " ! ?. If specific symbols are explicitly listed (e.g., '+', '-', '.'), then include ONLY the listed ones. chars = string.ascii_letters + string.digits + " ,-.;'\\\"!?"; s = "".join(rng.choices(chars, k=rng.randint(0, 200))). If symbols include backslash, double-quote, [, or ] in the allowed set, escape them with a backslash in the Python string so they don't break the string literal or the formatted input (which uses [ ] and ").
- Strings must be printed with double quotes around them (use json.dumps())
- For arrays, print them as JSON using json.dumps()
- For custom type objects, convert them to the input format expected by the runner (use the Custom Type Definitions above as a guide)
- For plain integers/strings/floats, just print() them directly
- Do NOT add unnecessary comments. Only add a single-line comment above each variable showing the variable range (e.g., # n: 2 to 10, target: -200 to 200)
- Output NO explanations, NO markdown — ONLY the Python code. The code must have a generate() function and an if __name__ == "__main__": block.

Example for Two Sum (twoSum(nums: array:integer, target: integer)):
```python
import random
import json
import sys

def generate():
    seed = int(sys.stdin.readline().strip())
    rng = random.Random(seed)
    n = rng.randint(2, 10)
    nums = [rng.randint(-100, 100) for _ in range(n)]
    i, j = rng.sample(range(n), 2)
    target = nums[i] + nums[j]
    print(json.dumps(nums))
    print(target)

if __name__ == "__main__":
    generate()
```"""

    try:
        content, provider = AIService.generate_with_fallback(prompt, ["gemini"])
        content = AIService.clean_json_string(content)
        # Save to problem model
        problem.generator_code = content
        problem.save(update_fields=["generator_code"])
        return JsonResponse({"code": content, "provider": provider})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


import json as _json


def save_generator_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    try:
        data = _json.loads(request.body)
        problem_id = data.get("problem_id")
        generator_code = data.get("generator_code", "")
        if not problem_id:
            return JsonResponse({"error": "Missing problem_id"}, status=400)
        problem = Problem.objects.get(id=problem_id)
        problem.generator_code = generator_code
        problem.save(update_fields=["generator_code"])
        return JsonResponse({"status": "ok"})
    except Problem.DoesNotExist:
        return JsonResponse({"error": "Problem not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def generate_programmatic_async(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    problem_id = request.POST.get("problem")
    generator_code = request.POST.get("generator_code", "").strip()
    generator_language = request.POST.get("generator_language", "PYTHON").strip()
    solution_code = request.POST.get("solution_code", "").strip()
    solution_language = request.POST.get("solution_language", "CPP").strip()
    count = int(request.POST.get("count", 20))

    if not generator_code or not solution_code:
        return JsonResponse(
            {"error": "Generator code and solution code are required"}, status=400
        )

    from problem.tasks import generate_testcases_programmatic_task

    task = generate_testcases_programmatic_task.delay(
        problem_id,
        generator_code,
        generator_language,
        solution_code,
        solution_language,
        count,
    )

    return JsonResponse({"status": "pending", "task_id": task.id})
