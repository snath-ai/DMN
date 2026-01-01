from __future__ import annotations
from typing import List, Dict, Optional, Union, Any, Literal
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum

# --- Enums ---

class NodeType(str, Enum):
    LLM = "LLMNode"
    TOOL = "ToolNode"
    ROUTER = "RouterNode"
    ADD_VALUE = "AddValueNode"
    CLEAR_ERROR = "ClearErrorNode"
    START = "StartNode"
    END = "EndNode"

# --- Core Models ---

class ChangeLogEntry(BaseModel):
    """
    Represents a single entry in the agent's change history.
    """
    version: str = Field(..., description="The semantic version of this change.")
    date: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the change.")
    author: str = Field(..., description="The author who made the change.")
    description: str = Field(..., description="A brief description of what changed.")

class AgentVersion(BaseModel):
    """
    Versioning information for the agent.
    """
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic Version (e.g., 1.0.0)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AgentMetadata(BaseModel):
    """
    Descriptive metadata for the agent.
    """
    name: str = Field(..., min_length=1, max_length=100)
    id: UUID = Field(default_factory=uuid4, description="Unique UUID for the agent.")
    description: Optional[str] = Field(None, max_length=1000)
    author: str = Field(..., description="The creator of the agent.")
    tags: List[str] = Field(default_factory=list)

class SecurityPolicy(BaseModel):
    """
    Security and resource limits for the agent.
    """
    allowed_tools: List[str] = Field(default_factory=list, description="List of allowed tool names.")
    max_tokens: int = Field(default=10000, ge=1, description="Maximum tokens per run.")
    cost_limit_usd: float = Field(default=1.0, ge=0.0, description="Maximum cost per run in USD.")
    max_steps: int = Field(default=50, ge=1, description="Maximum execution steps to prevent infinite loops.")

# --- Graph Models ---

class Position(BaseModel):
    x: float
    y: float

class BaseNodeModel(BaseModel):
    """
    Base model for all nodes in the graph.
    """
    id: str = Field(..., description="Unique identifier for the node within the graph.")
    type: NodeType
    label: Optional[str] = None
    position: Optional[Position] = None
    
    model_config = ConfigDict(extra="ignore")

class LLMNodeModel(BaseNodeModel):
    type: Literal[NodeType.LLM] = NodeType.LLM
    model_name: str
    prompt_template: str
    output_key: str
    system_instruction: Optional[str] = None
    max_retries: int = Field(default=3)

class ToolNodeModel(BaseNodeModel):
    type: Literal[NodeType.TOOL] = NodeType.TOOL
    tool_name: str
    input_keys: List[str]
    output_key: Optional[str] = None

class RouterNodeModel(BaseNodeModel):
    type: Literal[NodeType.ROUTER] = NodeType.ROUTER
    decision_field: str = Field(..., description="State key to check for routing decision.")
    routes: Dict[str, str] = Field(..., description="Map of decision values to Next Node IDs.")
    default_route: Optional[str] = Field(None, description="Node ID to fallback to.")

class AddValueNodeModel(BaseNodeModel):
    type: Literal[NodeType.ADD_VALUE] = NodeType.ADD_VALUE
    key: str
    value: Any

class GenericNodeModel(BaseNodeModel):
    """Fallback for other node types"""
    type: NodeType
    config: Dict[str, Any] = Field(default_factory=dict)

# Union of all specific node models
NodeModel = Union[LLMNodeModel, ToolNodeModel, RouterNodeModel, AddValueNodeModel, GenericNodeModel]

class Edge(BaseModel):
    """
    Represents a connection between two nodes.
    """
    source: str = Field(..., description="Source Node ID")
    target: str = Field(..., description="Target Node ID")
    label: Optional[str] = None
    handle: Optional[str] = Field(None, description="Source handle identifier (for routers).")

class Graph(BaseModel):
    """
    The executable graph structure.
    """
    nodes: List[NodeModel]
    edges: List[Edge]
    start_node: str = Field(..., description="ID of the entry point node.")

# --- Root Manifest ---

class AgentManifest(BaseModel):
    """
    LARASpec: The Root Object.
    Defines the complete specification for a Lár Agent.
    """
    metadata: AgentMetadata
    version_info: AgentVersion = Field(..., alias="version")
    changelog: List[ChangeLogEntry] = Field(default_factory=list)
    policy: SecurityPolicy = Field(default_factory=SecurityPolicy)
    graph: Graph
    min_lar_version: str = Field("1.0.0", description="Minimum Lár Engine version required.")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "metadata": {
                    "name": "My Agent",
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "author": "User"
                },
                "version": {
                    "version": "1.0.0"
                },
                "graph": {
                    "nodes": [],
                    "edges": [],
                    "start_node": "node_1"
                }
            }
        }
    )
