"""Shared schemas and types for Project Agent."""

from .document import (
    Document, DocumentMetadata, DocumentStatus, DocType, 
    DocumentCategory, DocumentSubcategory, ClassificationInfo
)
from .chat import ChatRequest, ChatResponse, Citation
from .admin import IngestRequest, IngestResponse, AdminAction
from .inventory import InventoryRequest, InventoryResponse, InventoryFilters

__all__ = [
    "Document",
    "DocumentMetadata", 
    "DocumentStatus",
    "DocType",
    "DocumentCategory",
    "DocumentSubcategory", 
    "ClassificationInfo",
    "ChatRequest",
    "ChatResponse",
    "Citation",
    "IngestRequest",
    "IngestResponse", 
    "AdminAction",
    "InventoryRequest",
    "InventoryResponse",
    "InventoryFilters",
]
