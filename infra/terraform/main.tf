# Project Agent - Terraform Infrastructure Configuration

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "transparent-agent-test"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "documentai.googleapis.com",
    "vision.googleapis.com",
    "aiplatform.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "identityplatform.googleapis.com",
    "drive.googleapis.com",
    "sheets.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "dlp.googleapis.com"
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
}

# Cloud Storage buckets
resource "google_storage_bucket" "documents" {
  name          = "ta-test-docs-${var.environment}"
  location      = "US"
  force_destroy = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_storage_bucket" "thumbnails" {
  name          = "ta-test-thumbs-${var.environment}"
  location      = "US"
  force_destroy = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Firestore database
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = "us-central1"
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# Pub/Sub topic and subscription for ingestion
resource "google_pubsub_topic" "ingestion" {
  name = "project-agent-ingestion"

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_subscription" "ingestion" {
  name  = "project-agent-ingestion-sub"
  topic = google_pubsub_topic.ingestion.name

  ack_deadline_seconds = 600

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  depends_on = [google_project_service.required_apis]
}

# Service account for ingestion
resource "google_service_account" "ingestor" {
  account_id   = "sa-ingestor"
  display_name = "Project Agent Ingestor"
  description  = "Service account for document ingestion operations"
}

# IAM bindings for service account
resource "google_project_iam_member" "ingestor_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_pubsub_editor" {
  project = var.project_id
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_documentai_user" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

resource "google_project_iam_member" "ingestor_vision_user" {
  project = var.project_id
  role    = "roles/ml.developer"
  member  = "serviceAccount:${google_service_account.ingestor.email}"
}

# Identity Platform configuration
resource "google_identity_platform_config" "default" {
  project = var.project_id

  sign_in {
    allow_duplicate_emails = false
  }

  sign_in {
    email {
      enabled           = true
      password_required = false
    }
  }

  sign_in {
    anonymous {
      enabled = false
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Vertex AI Vector Search index
resource "google_vertex_ai_index" "vector_search" {
  display_name = "project-agent-${var.environment}"
  description  = "Vector search index for Project Agent"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.documents.name}/vectors"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 150
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Scheduler for periodic Drive sync
resource "google_cloud_scheduler_job" "drive_sync" {
  name        = "project-agent-drive-sync"
  description = "Periodic Google Drive sync for Project Agent"
  schedule    = "*/15 * * * *" # Every 15 minutes
  time_zone   = "UTC"

  pubsub_target {
    topic_name = "projects/${var.project_id}/topics/${google_pubsub_topic.ingestion.name}"
    data = base64encode(jsonencode({
      action = "gdrive_sync"
      folder_ids = []
      recursive = true
    }))
  }

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "documents_bucket" {
  description = "Documents storage bucket"
  value       = google_storage_bucket.documents.name
}

output "thumbnails_bucket" {
  description = "Thumbnails storage bucket"
  value       = google_storage_bucket.thumbnails.name
}

output "pubsub_topic" {
  description = "Ingestion Pub/Sub topic"
  value       = google_pubsub_topic.ingestion.name
}

output "pubsub_subscription" {
  description = "Ingestion Pub/Sub subscription"
  value       = google_pubsub_subscription.ingestion.name
}

output "service_account_email" {
  description = "Ingestor service account email"
  value       = google_service_account.ingestor.email
}

output "vector_index_name" {
  description = "Vertex AI Vector Search index name"
  value       = google_vertex_ai_index.vector_search.name
}
