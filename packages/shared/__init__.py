"""Shared utilities and clients for Project Agent."""

from packages.shared.schemas.chat import ChatRequest, ChatResponse, Citation
from packages.shared.schemas.document import Document, DocumentMetadata
from packages.shared.schemas.inventory import InventoryRequest, InventoryResponse, InventoryFilters, InventoryItem

__all__ = [
    "ChatRequest",
    "ChatResponse", 
    "Citation",
    "Document",
    "DocumentMetadata",
    "InventoryRequest",
    "InventoryResponse",
    "InventoryFilters",
    "InventoryItem"
]

