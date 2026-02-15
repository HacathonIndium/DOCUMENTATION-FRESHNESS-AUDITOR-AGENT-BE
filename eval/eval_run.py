import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from langsmith import Client, evaluate
from langchain_openai import ChatOpenAI
from document_freshness_auditor.crew import DocumentFreshnessAuditor
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CREW EXECUTION WITH DETAILED LOGGING
# ============================================================

class CrewExecutionTracker:
    """Track crew execution with detailed metrics"""
    
    def __init__(self):
        self.execution_log = {
            "start_time": None,
            "end_time": None,
            "agents": {},
            "tasks": {},
            "tools": {},
            "errors": []
        }
    
    def log_agent_start(self, agent_name: str):
        """Log when an agent starts"""
        if agent_name not in self.execution_log["agents"]:
            self.execution_log["agents"][agent_name] = {
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "output": None,
                "status": "running"
            }
    
    def log_agent_end(self, agent_name: str, output: str):
        """Log when an agent finishes"""
        if agent_name in self.execution_log["agents"]:
            self.execution_log["agents"][agent_name]["end_time"] = datetime.now().isoformat()
            self.execution_log["agents"][agent_name]["output"] = output[:500]  # First 500 chars
            self.execution_log["agents"][agent_name]["status"] = "completed"
    
    def log_task_execution(self, task_name: str, agent_name: str, status: str):
        """Log task execution"""
        self.execution_log["tasks"][task_name] = {
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    
    def log_tool_usage(self, tool_name: str, success: bool, error: Optional[str] = None):
        """Log tool usage"""
        if tool_name not in self.execution_log["tools"]:
            self.execution_log["tools"][tool_name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "error_log": []
            }
        
        self.execution_log["tools"][tool_name]["calls"] += 1
        
        if success:
            self.execution_log["tools"][tool_name]["successes"] += 1
        else:
            self.execution_log["tools"][tool_name]["failures"] += 1
            if error:
                self.execution_log["tools"][tool_name]["error_log"].append(error)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics"""
        agents = self.execution_log["agents"]
        tools = self.execution_log["tools"]
        
        # Calculate agent success rates
        agent_metrics = {}
        for agent_name, data in agents.items():
            agent_metrics[agent_name] = {
                "completed": data["status"] == "completed",
                "had_output": bool(data["output"])
            }
        
        # Calculate tool success rates
        tool_metrics = {}
        for tool_name, data in tools.items():
            success_rate = (data["successes"] / data["calls"] * 100) if data["calls"] > 0 else 0
            tool_metrics[tool_name] = {
                "calls": data["calls"],
                "success_rate": success_rate,
                "failures": data["failures"]
            }
        
        return {
            "agents": agent_metrics,
            "tools": tool_metrics,
            "tasks": self.execution_log["tasks"]
        }

# Global tracker
_tracker = CrewExecutionTracker()

def run_crew_with_tracking(project_path: str, files_content: Dict) -> Dict:
    """Run crew and track execution"""
    global _tracker
    _tracker = CrewExecutionTracker()
    
    try:
        auditor = DocumentFreshnessAuditor()
        crew = auditor.crew()
        
        # Log agents
        for agent in crew.agents:
            _tracker.log_agent_start(agent.role)
        
        # Run crew
        result = crew.kickoff(inputs={
            "project_path": project_path,
            "files_content": files_content,
        })
        
        # Log completion
        for agent in crew.agents:
            _tracker.log_agent_end(agent.role, str(result))
        
        return {
            "output": str(result),
            "metrics": _tracker.get_metrics()
        }
    
    except Exception as e:
        _tracker.execution_log["errors"].append(str(e))
        return {
            "output": f"Error: {e}",
            "metrics": _tracker.get_metrics(),
            "error": str(e)
        }

# ============================================================
# AGENT-SPECIFIC EVALUATORS
# ============================================================

class CrewAgentEvaluators:
    """Evaluate individual agents in crew"""
    
    def __init__(self, judge_model: str = "gpt-oss-cloud", api_key: str = None):
        self.judge = ChatOpenAI(
            model_name=judge_model,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            temperature=0.1
        )
    
    def extract_score(self, response: str) -> float:
        """Extract score from LLM response"""
        import re
        try:
            patterns = [r'score[:\s]+(\d+)', r'(\d+)\s*(?:/100|%)']
            for pattern in patterns:
                match = re.search(pattern, response.lower())
                if match:
                    score = float(match.group(1))
                    return min(100, max(0, score)) / 100.0
        except:
            pass
        return 0.5
    
    def evaluate_auditor_agent(self, run, example) -> Optional[Dict]:
        """Evaluate: Documentation Auditor Agent
        
        Questions:
        - Did it find all issues? (Recall)
        - Did it find only real issues? (Precision)
        - Did it classify severity correctly? (Accuracy)
        """
        output = str(run.outputs.get("output", ""))
        metrics = run.outputs.get("metrics", {})
        
        expected_issues = example.outputs.get("total_issues", 22)
        
        prompt = f"""You are an expert evaluating a Documentation Auditor AI Agent.

AGENT TASK: Scan code and documentation to find all freshness issues.

GROUND TRUTH:
- Expected to find: {expected_issues} total issues
- Should classify as: Critical (3), Major (19), Minor (0)

AGENT OUTPUT (excerpt):
{output[:1000]}

AGENT EXECUTION METRICS:
{json.dumps(metrics, indent=2)}

EVALUATE the agent on:
1. RECALL: Did it find all {expected_issues} issues?
   - 0-20: Found <25% of issues
   - 20-40: Found 25-50% of issues
   - 40-60: Found 50-75% of issues
   - 60-80: Found 75-90% of issues
   - 80-100: Found 90-100% of issues

2. PRECISION: Did it avoid false positives?
   - 0-20: Many hallucinated issues
   - 20-40: Some false positives
   - 40-60: Mostly accurate
   - 60-80: Very accurate
   - 80-100: No false positives

3. ACCURACY: Correct severity classification?
   - 0-20: Mostly wrong
   - 20-40: Some correct
   - 40-60: Moderate accuracy
   - 60-80: Good accuracy
   - 80-100: Perfect accuracy

Overall Agent Quality Score (0-100):
Respond with: "Score: [0-100]"
"""
        
        print(f"   🤖 Evaluating Auditor Agent...")
        response = self.judge.invoke(prompt)
        score = self.extract_score(response.content if hasattr(response, 'content') else str(response))
        
        return {
            "key": "auditor_agent_quality",
            "score": score,
            "comment": f"Auditor Agent: {score:.0%}"
        }
    
    def evaluate_scorer_agent(self, run, example) -> Optional[Dict]:
        """Evaluate: Freshness Scorer Agent
        
        Questions:
        - Did it calculate freshness score correctly?
        - Are effort estimates accurate?
        """
        output = str(run.outputs.get("output", ""))
        
        expected_freshness = 34  # From ground truth
        expected_effort = 4.5  # hours
        
        prompt = f"""You are an expert evaluating a Freshness Scorer AI Agent.

AGENT TASK: Calculate documentation freshness score and effort estimates.

EXPECTED VALUES:
- Freshness score: {expected_freshness}%
- Effort to fix: {expected_effort} hours

AGENT OUTPUT (excerpt):
{output[:1000]}

EVALUATE the agent on:
1. SCORE ACCURACY: Is freshness score close to {expected_freshness}%?
   - Allow ±10% variance
   - Score: (100 - |actual - expected|) / 100

2. EFFORT ESTIMATE ACCURACY: Is effort close to {expected_effort}h?
   - Allow ±30% variance
   - Score: (100 - |actual - expected| * 100 / expected) / 100

3. REASONING QUALITY: Is reasoning clear and justified?
   - Score: 0-100

Overall Agent Quality (0-100):
Respond with: "Score: [0-100]"
"""
        
        print(f"   📊 Evaluating Scorer Agent...")
        response = self.judge.invoke(prompt)
        score = self.extract_score(response.content if hasattr(response, 'content') else str(response))
        
        return {
            "key": "scorer_agent_quality",
            "score": score,
            "comment": f"Scorer Agent: {score:.0%}"
        }
    
    def evaluate_fix_suggester_agent(self, run, example) -> Optional[Dict]:
        """Evaluate: Fix Suggester Agent
        
        Questions:
        - Are suggested fixes correct?
        - Are diffs valid and applicable?
        - Are suggestions actionable?
        """
        output = str(run.outputs.get("output", ""))
        
        prompt = f"""You are an expert evaluating a Fix Suggester AI Agent.

AGENT TASK: Generate correct, actionable code fixes for all issues.

CRITERIA:
1. CORRECTNESS: Are diffs syntactically valid?
2. APPLICABILITY: Can diffs be applied without errors?
3. COMPLETENESS: Are all issues addressed?
4. ACTIONABILITY: Can developers understand and implement fixes?
5. QUALITY: Are fixes best-practice and well-documented?

AGENT OUTPUT (excerpt):
{output[:1000]}

EVALUATE:
1. Diff Validity (0-100): Are all diffs syntactically correct?
2. Completeness (0-100): How many of ~22 issues are addressed?
3. Actionability (0-100): Can developers easily apply fixes?
4. Quality (0-100): Are fixes well-documented and best-practice?

Overall Agent Quality (0-100):
Respond with: "Score: [0-100]"
"""
        
        print(f"   🔧 Evaluating Fix Suggester Agent...")
        response = self.judge.invoke(prompt)
        score = self.extract_score(response.content if hasattr(response, 'content') else str(response))
        
        return {
            "key": "fixer_agent_quality",
            "score": score,
            "comment": f"Fix Suggester Agent: {score:.0%}"
        }

# ============================================================
# TOOL EVALUATORS
# ============================================================

def evaluate_tool_effectiveness(run, example) -> Optional[Dict]:
    """Evaluate: How well tools were used by agents"""
    metrics = run.outputs.get("metrics", {})
    tools = metrics.get("tools", {})
    
    if not tools:
        return {"key": "tool_effectiveness", "score": 0.5, "comment": "No tool metrics"}
    
    # Calculate average tool success rate
    success_rates = []
    for tool_name, data in tools.items():
        success_rate = data.get("success_rate", 0)
        success_rates.append(success_rate)
    
    avg_success = sum(success_rates) / len(success_rates) if success_rates else 0
    score = avg_success / 100.0
    
    print(f"   🔨 Evaluating Tool Effectiveness...")
    
    return {
        "key": "tool_effectiveness",
        "score": score,
        "comment": f"Tool Success Rate: {score:.0%}"
    }

# ============================================================
# MAIN EVALUATION
# ============================================================

def run_crew_agent_evaluation(project_path: str, judge_model: str = "gpt-oss-cloud"):
    """Run complete crew agent evaluation"""
    
    print("=" * 70)
    print("🚀 CrewAI Agent Performance Evaluation")
    print("=" * 70)
    
    # Initialize evaluators
    evaluators_obj = CrewAgentEvaluators(judge_model)
    
    # Load dataset
    client = Client()
    dataset = client.read_dataset(dataset_name="Doc_Freshness_Ground_Truth")
    
    # Define evaluators
    evaluators = [
        evaluators_obj.evaluate_auditor_agent,
        evaluators_obj.evaluate_scorer_agent,
        evaluators_obj.evaluate_fix_suggester_agent,
        evaluate_tool_effectiveness,
    ]
    
    print(f"\n📊 Agent Evaluators:")
    print(f"   1. 🤖 Auditor Agent (Recall, Precision, Accuracy)")
    print(f"   2. 📊 Scorer Agent (Score accuracy, Effort accuracy)")
    print(f"   3. 🔧 Fix Suggester Agent (Correctness, Actionability)")
    print(f"   4. 🔨 Tool Effectiveness (Success rates)\n")
    
    print(f"⏳ Running evaluation...\n")
    
    # Run evaluation
    results = evaluate(
        run_crew_with_tracking,
        data=dataset,
        evaluators=evaluators,
        experiment_prefix="crew-agent-performance",
        max_concurrency=1
    )
    
    print("\n" + "=" * 70)
    print("✅ Agent Evaluation Complete!")
    print("=" * 70)
    print("\n📊 Metrics Evaluated:")
    print("   ✓ Auditor Agent Quality")
    print("   ✓ Scorer Agent Quality")
    print("   ✓ Fix Suggester Agent Quality")
    print("   ✓ Tool Effectiveness")
    print("\n📈 View on LangSmith: https://smith.langchain.com/\n")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-path", "-p", required=True)
    parser.add_argument("--judge-model", "-m", default="gpt-oss-cloud")
    args = parser.parse_args()
    
    run_crew_agent_evaluation(args.project_path, args.judge_model)