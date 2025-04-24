#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
State management for the Export/Import agent flow.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class FlowMode(str, Enum):
    """Mode of operation for the agent flow."""
    EXPORT = "export"
    IMPORT = "import"


class ExportState(BaseModel):
    """State for export operations."""
    model_name: Optional[str] = None
    selected_fields: List[str] = Field(default_factory=list)
    filter_domain: List[Any] = Field(default_factory=list)
    limit: int = 1000
    offset: int = 0
    export_path: Optional[str] = None
    records: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int = 0
    exported_records: int = 0
    status: str = "pending"
    error: Optional[str] = None


class ImportState(BaseModel):
    """State for import operations."""
    model_name: Optional[str] = None
    import_path: Optional[str] = None
    field_mapping: Dict[str, str] = Field(default_factory=dict)
    records_to_import: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int = 0
    imported_records: int = 0
    updated_records: int = 0
    failed_records: int = 0
    create_if_not_exists: bool = True
    update_if_exists: bool = True
    status: str = "pending"
    error: Optional[str] = None
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)


class AgentState(BaseModel):
    """State for the Export/Import agent flow."""
    mode: FlowMode = FlowMode.EXPORT
    export_state: ExportState = Field(default_factory=ExportState)
    import_state: ImportState = Field(default_factory=ImportState)
    current_step: str = "initialize"
    history: List[str] = Field(default_factory=list)
    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "llmdb18"
    odoo_username: str = "admin"
    odoo_password: str = "admin"
    
    def get_current_state(self) -> Union[ExportState, ImportState]:
        """Get the current state based on the mode."""
        if self.mode == FlowMode.EXPORT:
            return self.export_state
        return self.import_state