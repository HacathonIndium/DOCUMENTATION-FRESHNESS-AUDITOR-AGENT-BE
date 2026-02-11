from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import os
from document_freshness_auditor.tools.doc_tools import (
    DocstringSignatureTool, 
    ReadmeStructureTool, 
    ApiImplementationTool, 
    CodeCommentTool,
    ListFilesTool
)

@CrewBase
class DocumentFreshnessAuditor():
    """DocumentFreshnessAuditor crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        self.llm = LLM(
            model=os.getenv("MODEL_NAME", "llama3.2:3b"),
            base_url=os.getenv("API_BASE")
        )

    @agent
    def documentation_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config['documentation_auditor'],
            tools=[
                DocstringSignatureTool(), 
                ReadmeStructureTool(), 
                ApiImplementationTool(), 
                CodeCommentTool(),
                ListFilesTool()
            ],
            llm=self.llm,
            verbose=True
        )

    @agent
    def freshness_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['freshness_analyst'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def fix_suggester(self) -> Agent:
        return Agent(
            config=self.agents_config['fix_suggester'],
            llm=self.llm,
            verbose=True
        )

    @task
    def audit_task(self) -> Task:
        return Task(
            config=self.tasks_config['audit_task'],
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
        )

    @task
    def suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config['suggestion_task'],
            output_file='freshness_audit_report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
