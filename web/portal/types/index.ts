export type DocumentType = 'PDF' | 'DOCX' | 'TXT' | 'MD' | 'HTML'
export type MediaType = 'text' | 'image'
export type DocumentStatus = 'uploaded' | 'pending_access' | 'access_approved' | 'processed' | 'indexed' | 'quarantined' | 'failed'
export type DocumentDesignation = 'sow' | 'timeline' | 'deliverables' | 'misc'

export interface Document {
  id: string
  title: string
  type: DocumentType
  upload_date: string
  size: number
  status: 'uploaded' | 'pending_access' | 'access_approved' | 'processed' | 'indexed' | 'quarantined' | 'failed'
  metadata?: {
    pages?: number
    author?: string
    created_date?: string
  }
}

export interface ChatRequest {
  query: string
  filters?: {
    doc_type?: DocumentType
    media_type?: MediaType
  }
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  query_time_ms: number
  total_results: number
}

export interface Citation {
  doc_id: string
  title: string
  uri: string
  page: number
  excerpt: string
  thumbnail?: string
  web_view_link?: string
}

export interface DocumentDetail {
  id: string
  title: string
  content: string
  metadata: {
    type: DocumentType
    size: number
    upload_date: string
    pages?: number
  }
  chunks: DocumentChunk[]
}

export interface DocumentChunk {
  id: string
  text: string
  page: number
  score: number
}

export interface InventoryItem {
  doc_id: string  // API returns doc_id, not id
  title: string
  doc_type: DocumentType
  media_type: MediaType
  status: DocumentStatus
  created_by: string
  created_at: string  // API returns created_at, not upload_date
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