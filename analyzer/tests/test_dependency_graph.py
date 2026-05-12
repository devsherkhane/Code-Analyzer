"""Smoke test for dependency_graph.py static import resolution."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dependency_graph import build_dependency_graph


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    src = root / "src"
    src.mkdir(parents=True, exist_ok=True)

    (src / "A.js").write_text("import B from './B';\nimport { c } from './C.js'\n", encoding="utf-8")
    (src / "B.js").write_text("export default function B() {}\n", encoding="utf-8")
    (src / "C.js").write_text("export const c = 1\n", encoding="utf-8")

    files_table = [
        {
            "file_id": 1,
            "file_name": "A.js",
            "path": str(src / "A.js"),
            "imports": [{"source": "./B", "name": "B"}, {"source": "./C.js", "name": "c"}],
            "exports": [],
        },
        {
            "file_id": 2,
            "file_name": "B.js",
            "path": str(src / "B.js"),
            "imports": [],
            "exports": [{"name": "default"}],
        },
        {
            "file_id": 3,
            "file_name": "C.js",
            "path": str(src / "C.js"),
            "imports": [],
            "exports": [{"name": "c"}],
        },
    ]

    graph = build_dependency_graph(files_table, str(root))
    conns = graph.get("connections", [])

    assert any(c.get("from_id") == 1 and c.get("to_id") == 2 and c.get("type") == "import" for c in conns)
    assert any(c.get("from_id") == 1 and c.get("to_id") == 3 and c.get("type") == "import" for c in conns)
    for c in conns:
        assert "name" in c and c["name"], "Each connection should have a non-empty name"
        assert isinstance(c.get("names", []), list), "Each connection should have a names list"

print("DEPENDENCY GRAPH TEST PASSED")

