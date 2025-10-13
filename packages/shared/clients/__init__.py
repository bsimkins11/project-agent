"""Shared clients for GCP services.

POC: Minimal imports to avoid dependency conflicts.
Services import clients directly as needed.
"""

from .auth import require_domain_auth, require_admin_auth

__all__ = [
    "require_domain_auth",
    "require_admin_auth",
]

# Services should import clients directly:
# from packages.shared.clients.firestore import FirestoreClient
# from packages.shared.clients.gcs import GCSClient
# from packages.shared.clients.pubsub import PubSubClient
# from packages.shared.clients.documentai import DocumentAIClient
# from packages.shared.clients.vision import VisionClient
# from packages.shared.clients.vector_search import VectorSearchClient
# from packages.shared.clients.drive import DriveClient
