export type DocumentType = 'PDF' | 'DOCX' | 'TXT' | 'MD' | 'HTML'
export type MediaType = 'text' | 'image'
export type DocumentStatus = 
  | 'uploaded' 
  | 'request_access' 
  | 'access_requested' 
  | 'access_granted' 
  | 'awaiting_approval' 
  | 'approved' 
  | 'processing_requested' 
  | 'processing' 
  | 'processed' 
  | 'quarantined' 
  | 'failed'

// Enhanced classification types
export type DocType = 
  // Project Management Documents
  | 'sow' | 'timeline' | 'deliverable' | 'milestone' | 'requirements' | 'specification'
  // Financial Documents
  | 'budget' | 'invoice' | 'expense' | 'financial_report'
  // Technical Documents
  | 'technical_doc' | 'api_doc' | 'user_guide' | 'architecture' | 'design_doc'
  // Communication Documents
  | 'email' | 'meeting_notes' | 'presentation' | 'report'
  // Legal and Compliance
  | 'contract' | 'legal_doc' | 'policy' | 'compliance'
  // Data and Analysis
  | 'data_sheet' | 'analysis' | 'research' | 'survey'
  // Media and Assets
  | 'image' | 'video' | 'audio' | 'diagram'
  // Miscellaneous
  | 'misc' | 'template' | 'form'

export type DocumentCategory = 
  | 'project_management' | 'financial' | 'technical' | 'communication' 
  | 'legal_compliance' | 'data_analysis' | 'media_assets' | 'miscellaneous'

export type DocumentSubcategory = 
  // Project Management subcategories
  | 'planning' | 'execution' | 'monitoring' | 'closure'
  // Financial subcategories
  | 'budgeting' | 'billing' | 'reporting' | 'audit'
  // Technical subcategories
  | 'development' | 'testing' | 'deployment' | 'maintenance'
  // Communication subcategories
  | 'internal' | 'external' | 'client' | 'stakeholder'
  // Legal/Compliance subcategories
  | 'contracts' | 'policies' | 'regulatory' | 'risk'
  // Data/Analysis subcategories
  | 'collection' | 'processing' | 'visualization' | 'insights'
  // Media/Assets subcategories
  | 'creative' | 'marketing' | 'training' | 'reference'

// Legacy type for backward compatibility
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

// Enhanced classification interfaces
export interface ClassificationInfo {
  doc_type: DocType
  category: DocumentCategory
  subcategory?: DocumentSubcategory
  confidence_score: number
  classification_method: string
  alternative_types: Array<{
    doc_type: string
    score: number
    keywords: string[]
  }>
  keywords: string[]
  last_classified_at?: string
}

export interface ClassificationOptions {
  doc_types: Array<{ value: string; label: string }>
  categories: Array<{ value: string; label: string }>
  subcategories: Array<{ value: string; label: string }>
}

export interface DocumentMetadata {
  id: string
  title: string
  type: string
  size: number
  uri: string
  status: string
  upload_date?: string
  processing_result?: Record<string, any>
  media_type?: MediaType
  doc_type?: DocType
  source_ref?: string
  source_uri?: string
  required_fields_ok: boolean
  dlp_scan?: {
    status: string
    findings: any[]
  }
  thumbnails: string[]
  embeddings?: {
    text: { count: number }
  }
  created_by?: string
  approved_by: string[]
  topics: string[]
  created_at?: string
  updated_at?: string
  classification?: ClassificationInfo
  auto_classified: boolean
  classification_reviewed: boolean
  classification_reviewed_by?: string
  classification_reviewed_at?: string
  // ... other fields as needed
}