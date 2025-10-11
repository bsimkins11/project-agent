'use client'

import { useState, useEffect } from 'react'
import { FolderIcon, PlusIcon, DocumentTextIcon, LinkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import apiClient from '@/lib/api-client'

interface Project {
  id: string
  client_id: string
  name: string
  code?: string
  status: string
  description?: string
  tags?: string[]
  document_index_url?: string
  document_count?: number
  created_at: string
}

interface Client {
  id: string
  name: string
}

export default function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [selectedClient, setSelectedClient] = useState<string>('')
  const [formData, setFormData] = useState({
    client_id: '',
    name: '',
    code: '',
    description: '',
    document_index_url: '',
    tags: ''
  })

  useEffect(() => {
    loadData()
  }, [selectedClient])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load clients for dropdown
      const clientsResponse = await apiClient.get<{ clients: Client[], total: number }>(
        '/api/admin/rbac/clients'
      )
      setClients(clientsResponse.clients)
      
      // Load projects (filtered by client if selected)
      const params = selectedClient ? `?client_id=${selectedClient}` : ''
      const projectsResponse = await apiClient.get<{ projects: Project[], total: number }>(
        `/api/admin/rbac/projects${params}`
      )
      setProjects(projectsResponse.projects)
    } catch (error) {
      toast.error('Failed to load data')
      console.error('Load error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const tags = formData.tags.split(',').map(t => t.trim()).filter(Boolean)
      
      const response = await apiClient.post<{ success: boolean, project_id: string, message: string }>(
        '/api/admin/rbac/projects',
        {
          ...formData,
          tags
        }
      )
      
      toast.success(response.message)
      setShowAddDialog(false)
      setFormData({
        client_id: '',
        name: '',
        code: '',
        description: '',
        document_index_url: '',
        tags: ''
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create project')
      console.error('Project creation error:', error)
    }
  }

  const handleImportDocuments = async (projectId: string) => {
    try {
      toast.loading('Importing documents from project index...')
      
      // Call the analyze-document-index endpoint with project context
      const project = projects.find(p => p.id === projectId)
      if (!project || !project.document_index_url) {
        toast.error('Project does not have a document index URL')
        return
      }
      
      const response = await apiClient.post<any>(
        '/api/admin/analyze-document-index',
        {
          index_url: project.document_index_url,
          project_id: project.id,
          client_id: project.client_id,
          index_type: 'sheets'
        }
      )
      
      toast.dismiss()
      toast.success(`Imported ${response.documents_created} documents!`)
      loadData() // Refresh to show updated document count
    } catch (error) {
      toast.dismiss()
      toast.error('Failed to import documents')
      console.error('Import error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <FolderIcon className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Project Management</h2>
            <p className="text-sm text-gray-600">Manage projects and their document indexes</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Add Project</span>
        </button>
      </div>

      {/* Client Filter */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Client
        </label>
        <select
          value={selectedClient}
          onChange={(e) => setSelectedClient(e.target.value)}
          className="w-full md:w-64 input-field"
        >
          <option value="">All Clients</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.name}
            </option>
          ))}
        </select>
      </div>

      {/* Projects List */}
      <div className="space-y-4">
        {loading ? (
          <div className="card">
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          </div>
        ) : projects.length === 0 ? (
          <div className="card text-center py-12">
            <FolderIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
            <p className="mt-1 text-sm text-gray-500">
              {selectedClient ? 'This client has no projects yet.' : 'Get started by creating a new project.'}
            </p>
            <button
              onClick={() => setShowAddDialog(true)}
              className="mt-4 btn-primary"
            >
              <PlusIcon className="h-5 w-5 inline mr-2" />
              Add First Project
            </button>
          </div>
        ) : (
          projects.map((project) => {
            const client = clients.find(c => c.id === project.client_id)
            return (
              <div key={project.id} className="card">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
                      {project.code && (
                        <span className="px-2 py-1 text-xs font-mono bg-gray-100 text-gray-700 rounded">
                          {project.code}
                        </span>
                      )}
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        project.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : project.status === 'completed'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {project.status}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1">
                      Client: <span className="font-medium">{client?.name || project.client_id}</span>
                    </p>
                    
                    {project.description && (
                      <p className="text-sm text-gray-600 mt-2">{project.description}</p>
                    )}
                    
                    <div className="flex items-center space-x-6 mt-3">
                      <div className="flex items-center space-x-2 text-sm">
                        <DocumentTextIcon className="h-4 w-4 text-gray-500" />
                        <span className="font-semibold text-gray-900">{project.document_count || 0}</span>
                        <span className="text-gray-600">documents</span>
                      </div>
                      
                      {project.document_index_url && (
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <LinkIcon className="h-4 w-4" />
                          <span>Index connected</span>
                        </div>
                      )}
                    </div>
                    
                    {project.tags && project.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {project.tags.map((tag, idx) => (
                          <span key={idx} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col space-y-2">
                    <button className="btn-secondary text-sm">
                      View Details
                    </button>
                    {project.document_index_url && (
                      <button
                        onClick={() => handleImportDocuments(project.id)}
                        className="btn-primary text-sm flex items-center justify-center space-x-1"
                      >
                        <DocumentTextIcon className="h-4 w-4" />
                        <span>Import Docs</span>
                      </button>
                    )}
                    <button className="btn-secondary text-sm">
                      Manage Users
                    </button>
                  </div>
                </div>
                
                {project.document_index_url && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">Document Index:</p>
                    <a
                      href={project.document_index_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 break-all"
                    >
                      {project.document_index_url}
                    </a>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Add Project Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Add New Project</h3>
            
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client *
                </label>
                <select
                  required
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  className="w-full input-field"
                >
                  <option value="">Select a client...</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full input-field"
                    placeholder="e.g., CHR MarTech Enablement"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Code
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full input-field"
                    placeholder="e.g., CHR-MT-001"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full input-field"
                  rows={2}
                  placeholder="Brief description of this project..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <span className="flex items-center space-x-2">
                    <LinkIcon className="h-4 w-4" />
                    <span>Document Index URL (Google Sheets) *</span>
                  </span>
                </label>
                <input
                  type="url"
                  required
                  value={formData.document_index_url}
                  onChange={(e) => setFormData({ ...formData, document_index_url: e.target.value })}
                  className="w-full input-field"
                  placeholder="https://docs.google.com/spreadsheets/d/..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  📊 This Google Sheet will be used to import all documents for this project
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full input-field"
                  placeholder="e.g., martech, enablement, sow1"
                />
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <span className="font-medium">💡 How it works:</span><br/>
                  Each project has its own Google Sheet with the document list. When you import, 
                  all documents from that sheet will be automatically assigned to this project.
                </p>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddDialog(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

