import apiClient from './api-client'
import { ChatRequest, ChatResponse, InventoryResponse, Document } from '@/types'

/**
 * Send chat message and get AI-generated response
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiClient.post<ChatResponse>('/api/chat/chat', request)
}

/**
 * Get document inventory with filtering and pagination
 */
export async function getInventory(params: {
  page?: number
  page_size?: number
  doc_type?: string
  media_type?: string
  status?: string
  q?: string
  created_by?: string
  topics?: string
}): Promise<InventoryResponse> {
  return apiClient.get<InventoryResponse>('/api/inventory', { params })
}

/**
 * Get document details by ID
 */
export async function getDocument(docId: string): Promise<Document> {
  return apiClient.get<Document>(`/api/documents/${docId}`)
}

/**
 * Ingest a single document from a link
 */
export async function ingestDocument(data: {
  title: string
  doc_type: string
  source_uri: string
  tags: string[]
  owner?: string
  version?: string
  overwrite?: boolean
  sow_number?: string
  deliverable?: string
  responsible_party?: string
  deliverable_id?: string
  confidence?: string
  link?: string
  notes?: string
}): Promise<{ ok: boolean; job_id: string; message: string }> {
  return apiClient.post<{ ok: boolean; job_id: string; message: string }>(
    '/api/admin/ingest/link', 
    data
  )
}

/**
 * Ingest multiple documents from CSV file
 */
export async function ingestCSV(file: File): Promise<{ ok: boolean; count: number; message: string }> {
  const formData = new FormData()
  formData.append('file', file)
  
  return apiClient.post<{ ok: boolean; count: number; message: string }>(
    '/api/admin/ingest/csv', 
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
}

/**
 * Sync documents from Google Drive folders
 */
export async function syncGoogleDrive(data: {
  folder_ids: string[]
  recursive: boolean
}): Promise<{ ok: boolean; job_id: string; folders_processed: number; files_found: number }> {
  return apiClient.post<{ ok: boolean; job_id: string; folders_processed: number; files_found: number }>(
    '/api/admin/gdrive/sync', 
    data
  )
}

/**
 * Assign document to a category
 */
export async function assignDocumentCategory(docId: string, category: string): Promise<{ success: boolean; doc_id: string; category: string; message: string }> {
  return apiClient.post<{ success: boolean; doc_id: string; category: string; message: string }>(
    `/api/admin/documents/${docId}/assign-category`,
    { category }
  )
}

/**
 * Get documents by category
 */
export async function getDocumentsByCategory(category: string): Promise<{
  category: string
  documents: Array<{
    id: string
    title: string
    type: string
    upload_date: string
    size: number
    status: string
    doc_type: string
    created_by?: string
    webViewLink?: string
    web_view_link?: string
    approved_by?: string
    approved_date?: string
  }>
  total: number
}> {
  return apiClient.get<any>(`/api/documents/by-category/${category}`)
}

/**
 * Get pending documents for approval
 */
export async function getPendingDocuments(): Promise<{
  documents: Array<{
    id: string
    title: string
    source_uri: string
    doc_type: string
    upload_date: string
    status: string
    created_by: string
    web_view_link: string
  }>
  total: number
}> {
  return apiClient.get<any>('/api/admin/documents/pending')
}

/**
 * Approve a document
 */
export async function approveDocument(docId: string, docType?: string): Promise<{
  success: boolean
  doc_id: string
  status: string
  message: string
}> {
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/approve`,
    { doc_type: docType }
  )
}

/**
 * Reject a document
 */
export async function rejectDocument(docId: string, reason?: string): Promise<{
  success: boolean
  doc_id: string
  status: string
  message: string
}> {
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/reject`,
    { reason }
  )
}

/**
 * Delete a document
 */
export async function deleteDocument(docId: string): Promise<{
  success: boolean
  doc_id: string
  deleted_document: any
  message: string
}> {
  return apiClient.delete<any>(`/api/admin/documents/${docId}`)
}

/**
 * Check for duplicate document
 */
export async function checkDuplicateDocument(data: {
  title: string
  source_uri: string
}): Promise<{
  is_duplicate: boolean
  existing_document?: {
    id: string
    title: string
    source_uri: string
    doc_type: string
    upload_date: string
    status: string
  }
}> {
  return apiClient.post<any>('/api/admin/check-duplicate', data)
}

/**
 * Analyze document index (Google Sheets)
 */
export async function analyzeDocumentIndex(data: {
  index_url: string
  index_type?: string
}): Promise<{
  success: boolean
  documents_created: number
  documents: Array<{
    id: string
    title: string
    source_uri: string
    doc_type: string
    upload_date: string
    status: string
    created_by: string
    web_view_link: string
    sow_number: string
    deliverable: string
    responsible_party: string
    deliverable_id: string
    confidence: string
    link: string
    notes: string
    from_index: boolean
    index_source: string
  }>
  message: string
}> {
  return apiClient.post<any>('/api/admin/analyze-document-index', data)
}

/**
 * Add URL to a document
 */
export async function addDocumentUrl(docId: string, data: {
  source_uri?: string
  upload_file?: File
}): Promise<{
  success: boolean
  doc_id: string
  source_uri: string
  status: string
  message: string
}> {
  const formData = new FormData()
  if (data.source_uri) {
    formData.append('source_uri', data.source_uri)
  }
  if (data.upload_file) {
    formData.append('upload_file', data.upload_file)
  }
  
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/add-url`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
}

/**
 * Update document metadata
 */
export async function updateDocumentMetadata(docId: string, data: {
  title?: string
  doc_type?: string
  sow_number?: string
  deliverable?: string
  responsible_party?: string
  deliverable_id?: string
  confidence?: string
  link?: string
  notes?: string
}): Promise<{
  success: boolean
  doc_id: string
  message: string
}> {
  return apiClient.post<any>(`/api/admin/documents/${docId}/update-metadata`, data)
}

/**
 * Grant document permission
 */
export async function grantDocumentPermission(docId: string, data?: {
  notes?: string
}): Promise<{
  success: boolean
  doc_id: string
  status: string
  permission_status: string
  message: string
}> {
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/grant-permission`,
    data || {}
  )
}

/**
 * Deny document permission
 */
export async function denyDocumentPermission(docId: string, data?: {
  reason?: string
}): Promise<{
  success: boolean
  doc_id: string
  status: string
  permission_status: string
  message: string
}> {
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/deny-permission`,
    data || {}
  )
}

/**
 * Request access to a document
 */
export async function requestDocumentAccess(docId: string, data?: {
  message?: string
}): Promise<{
  success: boolean
  access_request: {
    id: string
    document_id: string
    document_title: string
    document_url: string
    drive_file_id: string
    requested_by: string
    requested_at: string
    status: string
    message: string
    access_type: string
    permissions_requested: string[]
  }
  document: {
    id: string
    title: string
    status: string
    access_requested: boolean
    access_requested_at: string | null
  }
  message: string
  next_steps: string[]
}> {
  return apiClient.post<any>(
    `/api/admin/documents/${docId}/request-access`,
    data || {}
  )
}
