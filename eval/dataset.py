import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

def create_dataset():
    """Create ground truth dataset matching freshness_audit_report.md"""
    
    client = Client()
    dataset_name = "Doc_Freshness_Ground_Truth"
    
    # Delete existing dataset if it exists
    try:
        client.delete_dataset(dataset_name=dataset_name)
        print(f"🗑️  Deleted existing dataset: {dataset_name}\n")
    except:
        pass
    
    # Create new dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Ground truth for documentation freshness audit evaluation"
    )
    
    print(f"✅ Created dataset: {dataset_name}\n")
    
    # Define ground truth: Expected issues from audit report
    ground_truth = {
        "inputs": {
            "project_path": "/Users/vinaypodeti/Desktop/Document-Freshness-Auditor_agent/DOCUMENTATION-FRESHNESS-AUDITOR-AGENT-BE/src/document_freshness_auditor/demo-project",
            "files": ["api.py", "calculator.py", "README.md"]
        },
        "outputs": {
            # CRITICAL ISSUES (3 total)
            "critical_issues": [
                {
                    "id": "CRIT-001",
                    "type": "missing_docstring",
                    "file": "calculator.py",
                    "function": "factorial",
                    "description": "Missing docstring for factorial function",
                    "impact": "IDE hover-help unavailable, API unclear"
                },
                {
                    "id": "CRIT-002",
                    "type": "unimplemented_endpoint",
                    "file": "api.py",
                    "endpoint": "/calculate",
                    "description": "OpenAPI endpoint declared but not implemented",
                    "impact": "Clients get 404 errors, breaks integration tests"
                },
                {
                    "id": "CRIT-003",
                    "type": "unimplemented_endpoint",
                    "file": "api.py",
                    "endpoint": "/history",
                    "description": "OpenAPI endpoint declared but not implemented",
                    "impact": "Clients get 404 errors, breaks contract"
                }
            ],
            
            # MAJOR ISSUES (19 total)
            "major_issues": [
                {
                    "id": "MAJ-001",
                    "type": "stale_docstring",
                    "file": "api.py",
                    "function": "calculate",
                    "description": "Docstring lists wrong parameter 'x' instead of 'a' and 'b'",
                    "impact": "API contract mismatch, misleading IDE help"
                },
                {
                    "id": "MAJ-002",
                    "type": "missing_params_in_docstring",
                    "file": "api.py",
                    "function": "power_endpoint",
                    "description": "Missing 'base' and 'exponent' parameter documentation",
                    "impact": "Developers don't know what parameters to pass"
                },
                {
                    "id": "MAJ-003",
                    "type": "missing_params_in_docstring",
                    "file": "api.py",
                    "function": "batch_calculate",
                    "description": "Missing 'requests' parameter description",
                    "impact": "API usage unclear, onboarding friction"
                },
                {
                    "id": "MAJ-004",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "add",
                    "description": "Docstring missing parameter 'b', no return type hint",
                    "impact": "Incomplete API documentation"
                },
                {
                    "id": "MAJ-005",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "subtract",
                    "description": "Missing 'absolute' parameter in docstring",
                    "impact": "New parameter not documented"
                },
                {
                    "id": "MAJ-006",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "multiply",
                    "description": "Missing 'precision' parameter in docstring",
                    "impact": "Parameter behavior unclear"
                },
                {
                    "id": "MAJ-007",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "divide",
                    "description": "Missing 'safe' parameter and incorrect Raises section",
                    "impact": "Behavior change not documented"
                },
                {
                    "id": "MAJ-008",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "power",
                    "description": "Missing parameters 'base', 'exponent', 'mod' documentation",
                    "impact": "Function signature mismatch with docs"
                },
                {
                    "id": "MAJ-009",
                    "type": "stale_docstring",
                    "file": "calculator.py",
                    "function": "fibonacci",
                    "description": "Missing 'n' and 'memo' parameter documentation",
                    "impact": "Function contract unclear"
                },
                {
                    "id": "MAJ-010",
                    "type": "stale_reference",
                    "file": "README.md",
                    "reference": "requires 'requirements.txt'",
                    "description": "Project now uses Poetry, requirements.txt outdated",
                    "impact": "Installation instructions fail"
                },
                {
                    "id": "MAJ-011",
                    "type": "stale_reference",
                    "file": "README.md",
                    "reference": "utils.py and helpers.py",
                    "description": "Files mentioned but don't exist in codebase",
                    "impact": "Users look for non-existent modules"
                },
                {
                    "id": "MAJ-012",
                    "type": "missing_info",
                    "file": "README.md",
                    "section": "Setup",
                    "description": "config.yaml location not specified",
                    "impact": "Users don't know where to place config"
                },
                {
                    "id": "MAJ-013",
                    "type": "stale_reference",
                    "file": "README.md",
                    "reference": "tests/ directory location",
                    "description": "Tests directory not documented clearly",
                    "impact": "Running tests unclear"
                },
                {
                    "id": "MAJ-014",
                    "type": "stale_reference",
                    "file": "README.md",
                    "reference": "calculator.py path",
                    "description": "Path listed as '/src/calculator.py' but is actually 'demo-project/calculator.py'",
                    "impact": "Wrong path confuses developers"
                },
                {
                    "id": "MAJ-015",
                    "type": "missing_info",
                    "file": "README.md",
                    "section": "Endpoints",
                    "description": "/calculate and /history endpoints not implemented but documented",
                    "impact": "API contract broken"
                },
                {
                    "id": "MAJ-016",
                    "type": "missing_info",
                    "file": "api.py",
                    "section": "OpenAPI",
                    "description": "/batch endpoint declared but not aligned with current code",
                    "impact": "OpenAPI spec mismatch"
                },
                {
                    "id": "MAJ-017",
                    "type": "missing_info",
                    "file": "api.py",
                    "section": "OpenAPI",
                    "description": "/power endpoint declared but not aligned with current code",
                    "impact": "OpenAPI spec mismatch"
                },
                {
                    "id": "MAJ-018",
                    "type": "missing_section",
                    "file": "README.md",
                    "section": "Configuration",
                    "description": "Configuration section needs expansion with new location details",
                    "impact": "Setup incomplete"
                },
                {
                    "id": "MAJ-019",
                    "type": "incomplete_section",
                    "file": "README.md",
                    "section": "Running the demo",
                    "description": "Instructions for running tests and examples are vague",
                    "impact": "Onboarding friction"
                }
            ],
            
            # SUMMARY STATISTICS
            "total_critical": 3,
            "total_major": 19,
            "total_minor": 0,
            "total_issues": 22,
            "freshness_score": 34,
            "estimated_effort_hours": 4.5,
            
            # FILES AFFECTED
            "files_affected": {
                "api.py": {
                    "critical": 2,
                    "major": 3,
                    "freshness_score": 31
                },
                "calculator.py": {
                    "critical": 1,
                    "major": 6,
                    "freshness_score": 30
                },
                "README.md": {
                    "critical": 0,
                    "major": 10,
                    "freshness_score": 40
                }
            }
        }
    }
    
    # Add example to dataset
    example = client.create_example(
        inputs=ground_truth["inputs"],
        outputs=ground_truth["outputs"],
        dataset_id=dataset.id
    )
    
    print(f"✅ Added ground truth example to dataset\n")
    print(f"📊 Ground Truth Summary:")
    print(f"   • Critical issues: {ground_truth['outputs']['total_critical']}")
    print(f"   • Major issues: {ground_truth['outputs']['total_major']}")
    print(f"   • Total issues: {ground_truth['outputs']['total_issues']}")
    print(f"   • Average freshness: {ground_truth['outputs']['freshness_score']}%")
    print(f"   • Effort to fix: {ground_truth['outputs']['estimated_effort_hours']}h\n")
    
    print(f"✅ Dataset ready at: https://smith.langchain.com/o/datasets/{dataset.id}")
    print(f"\nNow run evaluation:")
    print(f"   uv run eval/eval_run.py --project-path /path/to/project\n")

if __name__ == "__main__":
    create_dataset()