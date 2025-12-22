import os, uuid, subprocess, shutil
from rest_framework.decorators import api_view
from rest_framework.response import Response

BASE_DIR = "/tmp/code-engine"

LANG_CONFIG = {
    "cpp": {
        "image": "runner-cpp",
        "file": "main.cpp",
        "cmd": "g++ main.cpp -O2 -o main && timeout 2s ./main"
    },
    "python": {
        "image": "runner-python",
        "file": "main.py",
        "cmd": "timeout 2s python3 main.py"
    },
    "java": {
        "image": "runner-java",
        "file": "Main.java",
        "cmd": "javac Main.java && timeout 2s java Main"
    },
    "javascript": {
        "image": "runner-node",
        "file": "main.js",
        "cmd": "timeout 2s node main.js"
    },
    "typescript": {
        "image": "runner-node",
        "file": "main.ts",
        "cmd": (
            "tsc main.ts --target ES2020 --module commonjs "
            "--outDir dist && timeout 2s node dist/main.js"
        )
    }
}

@api_view(["POST"])
def run_code(request):
    language = request.data.get("language")
    code = request.data.get("code")

    if language not in LANG_CONFIG:
        return Response({"error": "Unsupported language"}, status=400)

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE_DIR, job_id)
    os.makedirs(job_dir)

    cfg = LANG_CONFIG[language]
    file_path = os.path.join(job_dir, cfg["file"])
    with open(file_path, "w") as f:
        f.write(code)

    docker_cmd = [
        "docker", "run", "--rm",
        "--cpus=1",
        "--memory=128m",
        "-v", f"{job_dir}:/app",
        cfg["image"],
        "bash", "-c", cfg["cmd"]
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            text=True
        )
        output = result.stdout
        error = result.stderr
    except subprocess.TimeoutExpired:
        output, error = "", "Time Limit Exceeded"
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)

    return Response({
        "output": output,
        "error": error
    })
