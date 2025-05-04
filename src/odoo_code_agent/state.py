
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class AgentPhase(str, Enum):
    """Phase of operation for the agent flow."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    HUMAN_FEEDBACK_1 = "human_feedback_1"
    CODING = "coding"
    HUMAN_FEEDBACK_2 = "human_feedback_2"
    FINALIZATION = "finalization"


class AnalysisState(BaseModel):
    """State for analysis operations."""
    query: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    odoo_version: str = "18.0"
    documentation_results: List[Dict[str, Any]] = Field(default_factory=list)
    analysis_complete: bool = False
    error: Optional[str] = None


class PlanningState(BaseModel):
    """State for planning operations."""
    plan: str = ""
    tasks: List[str] = Field(default_factory=list)
    planning_complete: bool = False
    error: Optional[str] = None


class CodingState(BaseModel):
    """State for coding operations."""
    module_name: str = ""
    module_structure: Dict[str, Any] = Field(default_factory=dict)
    files_to_create: List[Dict[str, Any]] = Field(default_factory=list)
    files_created: List[str] = Field(default_factory=list)
    coding_complete: bool = False
    error: Optional[str] = None


class FeedbackState(BaseModel):
    """State for feedback operations."""
    feedback: str = ""
    feedback_processed: bool = False
    changes_required: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class OdooCodeAgentState(BaseModel):
    """State for the Odoo Code Agent flow."""
    phase: AgentPhase = AgentPhase.ANALYSIS
    analysis_state: AnalysisState = Field(default_factory=AnalysisState)
    planning_state: PlanningState = Field(default_factory=PlanningState)
    coding_state: CodingState = Field(default_factory=CodingState)
    feedback_state: FeedbackState = Field(default_factory=FeedbackState)
    current_step: str = "initialize"
    history: List[str] = Field(default_factory=list)
    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "llmdb18"
    odoo_username: str = "admin"
    odoo_password: str = "admin"
    
    def get_current_state(self) -> Union[AnalysisState, PlanningState, CodingState, FeedbackState]:
        """Get the current state based on the phase."""
        if self.phase == AgentPhase.ANALYSIS:
            return self.analysis_state
        elif self.phase == AgentPhase.PLANNING:
            return self.planning_state
        elif self.phase in [AgentPhase.CODING, AgentPhase.FINALIZATION]:
            return self.coding_state
        return self.feedback_state

