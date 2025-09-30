import axios from 'axios'
import { ChatRequest, ChatResponse, InventoryResponse, Document } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8081'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests (placeholder for now)
api.interceptors.request.use((config) => {
  // In production, add the auth token from localStorage or context
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post('/chat', request)
  return response.data
}

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
  const response = await api.get('/inventory', { params })
  return response.data
}

export async function getDocument(docId: string): Promise<Document> {
  const response = await api.get(`/documents/${docId}`)
  return response.data
}

export async function ingestDocument(data: {
  title: string
  doc_type: string
  source_uri: string
  tags: string[]
  owner?: string
  version?: string
}): Promise<{ ok: boolean; job_id: string; message: string }> {
  const response = await api.post('/admin/ingest/link', data)
  return response.data
}

export async function ingestCSV(file: File): Promise<{ ok: boolean; count: number; message: string }> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/admin/ingest/csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export async function syncGoogleDrive(data: {
  folder_ids: string[]
  recursive: boolean
}): Promise<{ ok: boolean; job_id: string; folders_processed: number; files_found: number }> {
  const response = await api.post('/admin/gdrive/sync', data)
  return response.data
}
