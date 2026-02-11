import os
import ast
import re
from typing import List, Dict, Any
from crewai.tools import BaseTool
from pydantic import Field

class DocstringSignatureTool(BaseTool):
    name: str = "Docstring Signature Auditor"
    description: str = "Compares function signatures with their docstrings to identify missing parameters or type mismatches."

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
        
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                signature_args = [arg.arg for arg in node.args.args if arg.arg != 'self']
                docstring = ast.get_docstring(node)
                
                if docstring:
                    # Very basic check: are all signature args mentioned in docstring?
                    missing_in_doc = [arg for arg in signature_args if arg not in docstring]
                    if missing_in_doc:
                        results.append(f"Function '{func_name}': Docstring is missing parameters: {', '.join(missing_in_doc)}")
                else:
                    results.append(f"Function '{func_name}': Missing docstring entirely.")
        
        return "\n".join(results) if results else "All function signatures match their docstrings in this file."

class ReadmeStructureTool(BaseTool):
    name: str = "README Structure Auditor"
    description: str = "Compares file/directory mentions in README with actual project structure."

    def _run(self, root_dir: str) -> str:
        readme_path = os.path.join(root_dir, "README.md")
        if not os.path.exists(readme_path):
            return "README.md not found in root directory."
        
        with open(readme_path, "r") as f:
            content = f.read()
        
        # Look for patterns that look like file paths or names
        mentions = re.findall(r'`([^`]+\.[a-z]+)`', content)
        results = []
        for mention in mentions:
            # Check if mentioned file exists relative to root
            if not os.path.exists(os.path.join(root_dir, mention)):
                results.append(f"README mentions `{mention}`, but it does not exist.")
        
        return "\n".join(results) if results else "All files mentioned in README exist."

class ApiImplementationTool(BaseTool):
    name: str = "API Implementation Auditor"
    description: str = "Placeholder for comparing API specs with implementation. Currently checks for existence of FastAPI/Flask routes."

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
        
        with open(file_path, "r") as f:
            content = f.read()
        
        # Simple regex for common route decorators
        routes = re.findall(r'@(?:app|router)\.(?:get|post|put|delete|patch)\("([^"]+)"\)', content)
        return f"Found routes in implementation: {', '.join(routes)}" if routes else "No API routes found in this file."

class CodeCommentTool(BaseTool):
    name: str = "Code Comment Auditor"
    description: str = "Extracts inline comments and surrounding code for LLM-based verification of correctness."

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
        
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        comments_with_context = []
        for i, line in enumerate(lines):
            if "#" in line:
                context = lines[max(0, i-2):min(len(lines), i+3)]
                comments_with_context.append({
                    "line_number": i + 1,
                    "comment": line.strip(),
                    "context": "".join(context)
                })
        
        return str(comments_with_context) if comments_with_context else "No inline comments found."

class ListFilesTool(BaseTool):
    name: str = "List Files Tool"
    description: str = "Recursively lists all files in a given directory to help identify which files need auditing."

    def _run(self, directory: str) -> str:
        if not os.path.exists(directory):
            return f"Error: Directory {directory} not found."
        
        file_list = []
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories like .git
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if not file.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, file), directory)
                    file_list.append(rel_path)
        
        return "\n".join(file_list) if file_list else "No files found in the directory."
