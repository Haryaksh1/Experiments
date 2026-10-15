# Run the same questions through all five RAG scripts and compare token usage
import os
import re
import subprocess
import sys

scripts = {
    "vector": "src/vector_rag.py",
    "keyword": "src/keyword_rag.py",
    "hybrid": "src/hybrid_rag.py",
    "tree": "src/tree_rag.py",
    "graph": "src/graph_rag.py",
}

questions = [
    "What is the punishment for theft under the BNS?",
    "What does the BSA say primary evidence means?",
    "What is included in secondary evidence under the BSA?",
    "When may a private person arrest someone under the BNSS?",
    "Under the BNSS, what happens if an arrested person's true name and residence are not ascertained within twenty-four hours?",
    "What is the corporate tax rate for pharmaceutical companies in India?",
]

# Each script reads questions from input(), so feed them through stdin
stdin = "\n".join(questions) + "\nexit\n"

results = {}
for name, path in scripts.items():
    print(f"Running {name} RAG...", flush=True)
    out = subprocess.run(
        [sys.executable, path],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    ).stdout
    counts = re.findall(r"Tokens: (\d+) in, (\d+) out, (\d+) total", out)
    results[name] = [tuple(map(int, c)) for c in counts]

print(f"\nTokens per question, averaged over {len(questions)} questions\n")
print(f"{'RAG':<10}{'Input':>8}{'Output':>8}{'Total':>8}")
for name, counts in results.items():
    if not counts:
        print(f"{name:<10}  no token counts found")
        continue
    avg = [sum(c[i] for c in counts) / len(counts) for i in range(3)]
    print(f"{name:<10}{avg[0]:>8.0f}{avg[1]:>8.0f}{avg[2]:>8.0f}")
