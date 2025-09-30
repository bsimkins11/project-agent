"""Shared clients for GCP services."""

from .auth import require_domain_auth, require_admin_auth
from .firestore import FirestoreClient
from .gcs import GCSClient
from .pubsub import PubSubClient
from .documentai import DocumentAIClient
from .vision import VisionClient
from .vector_search import VectorSearchClient
from .drive import DriveClient

__all__ = [
    "require_domain_auth",
    "require_admin_auth",
    "FirestoreClient",
    "GCSClient", 
    "PubSubClient",
    "DocumentAIClient",
    "VisionClient",
    "VectorSearchClient",
    "DriveClient",
]
