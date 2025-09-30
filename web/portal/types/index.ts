export type DocumentType = 'sow' | 'timeline' | 'deliverable' | 'misc'
export type MediaType = 'document' | 'image'
export type DocumentStatus = 'uploaded' | 'approved' | 'indexed' | 'quarantined' | 'failed'

export interface Citation {
  doc_id: string
  title: string
  uri: string
  page?: number
  excerpt: string
  thumbnail?: string
}

export interface ChatRequest {
  query: string
  filters?: {
    doc_type?: DocumentType
    media_type?: MediaType
  }
  max_results?: number
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  query_time_ms: number
  total_results: number
}

export interface InventoryItem {
  doc_id: string
  title: string
  doc_type: DocumentType
  media_type: MediaType
  status: DocumentStatus
  created_by: string
  created_at: string
  topics: string[]
  thumbnail?: string
}

export interface InventoryResponse {
  items: InventoryItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Document {
  metadata: {
    doc_id: string
    media_type: MediaType
    doc_type: DocumentType
    title: string
    uri: string
    source_ref: string
    status: DocumentStatus
    required_fields_ok: boolean
    dlp_scan: {
      status: string
      findings: any[]
    }
    thumbnails: string[]
    embeddings: {
      text: {
        count: number
      }
    }
    created_by: string
    approved_by: string[]
    topics: string[]
    created_at: string
    updated_at: string
  }
  content?: string
  chunks: string[]
  vector_ids: string[]
}

export interface IngestRequest {
  title: string
  doc_type: DocumentType
  source_uri: string
  tags: string[]
  owner?: string
  version?: string
}

export interface DriveSyncRequest {
  folder_ids: string[]
  recursive: boolean
}
