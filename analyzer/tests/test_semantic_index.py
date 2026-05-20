import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_index_builder import get_blast_radius, search_semantic_index


def test_semantic_search_ranks_relevant_files():
    index = {
        "by_id": {
            "1": {
                "file_id": "1",
                "file_name": "LoginView.vue",
                "path": "/tmp/LoginView.vue",
                "semantic_vector": [1.0, 0.0, 0.0],
            },
            "2": {
                "file_id": "2",
                "file_name": "AuthService.js",
                "path": "/tmp/AuthService.js",
                "semantic_vector": [0.0, 1.0, 0.0],
            },
        }
    }

    from mcp_index_builder import _compute_semantic_vector

    index["by_id"]["1"]["semantic_vector"] = _compute_semantic_vector("login auth user password")
    index["by_id"]["2"]["semantic_vector"] = _compute_semantic_vector("payment invoice billing")

    results = search_semantic_index(index, "login auth bug", top_k=2)
    assert results
    assert results[0]["file_name"] == "LoginView.vue"


def test_blast_radius_returns_downstream_and_upstream():
    index = {
        "dependency_graph": {
            "impact_map": {
                "1": [2, 3],
                "2": [4],
            },
            "file_map": {
                "1": {"name": "A.vue", "path": "/tmp/A.vue"},
                "2": {"name": "B.vue", "path": "/tmp/B.vue"},
                "3": {"name": "C.vue", "path": "/tmp/C.vue"},
                "4": {"name": "D.vue", "path": "/tmp/D.vue"},
            },
            "connections": [
                {"from_id": 1, "to_id": 9, "type": "import", "name": "Imports SharedThing"},
            ],
        }
    }

    result = get_blast_radius(index, file_id="1", depth=2)
    assert result["downstream_count"] == 3
    assert any(item["file_name"] == "D.vue" for item in result["downstream"])
    assert result["upstream_dependencies"][0]["file_id"] == "9"
