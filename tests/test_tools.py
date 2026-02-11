import unittest
import os
import shutil
import tempfile
from document_freshness_auditor.tools.doc_tools import DocstringSignatureTool, ReadmeStructureTool

class TestTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_docstring_signature_tool(self):
        # Create a temporary python file with a mismatch
        p = os.path.join(self.test_dir, "test.py")
        with open(p, "w") as f:
            f.write("""
def my_func(a, b):
    \"\"\"
    This docstring only mentions a.
    :param a: something
    \"\"\"
    return a + b
""")
        
        tool = DocstringSignatureTool()
        result = tool._run(p)
        self.assertIn("missing parameters: b", result)

    def test_readme_structure_tool(self):
        # Create a dummy README and check for missing files
        readme = os.path.join(self.test_dir, "README.md")
        with open(readme, "w") as f:
            f.write("Check out `missing_file.py` and `existing_file.py`.")
        
        existing = os.path.join(self.test_dir, "existing_file.py")
        with open(existing, "w") as f:
            f.write("print('hello')")
        
        tool = ReadmeStructureTool()
        result = tool._run(self.test_dir)
        self.assertIn("mentions `missing_file.py`, but it does not exist", result)
        self.assertNotIn("existing_file.py", result)

if __name__ == '__main__':
    unittest.main()
