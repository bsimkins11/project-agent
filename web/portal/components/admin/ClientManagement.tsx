'use client'

import { useState, useEffect } from 'react'
import { BuildingOfficeIcon, PlusIcon, UsersIcon, FolderIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import apiClient from '@/lib/api-client'

interface Client {
  id: string
  name: string
  domain?: string
  status: string
  contact_email?: string
  contact_name?: string
  industry?: string
  notes?: string
  created_at: string
}

interface ClientWithStats extends Client {
  project_count?: number
  user_count?: number
}

export default function ClientManagement() {
  const [clients, setClients] = useState<ClientWithStats[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    contact_email: '',
    contact_name: '',
    industry: '',
    notes: ''
  })

  useEffect(() => {
    loadClients()
  }, [])

  const loadClients = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get<{ clients: ClientWithStats[], total: number }>(
        '/api/admin/rbac/clients'
      )
      setClients(response.clients)
    } catch (error) {
      toast.error('Failed to load clients')
      console.error('Client load error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const response = await apiClient.post<{ success: boolean, client_id: string, message: string }>(
        '/api/admin/rbac/clients',
        formData
      )
      
      toast.success(response.message)
      setShowAddDialog(false)
      setFormData({
        name: '',
        domain: '',
        contact_email: '',
        contact_name: '',
        industry: '',
        notes: ''
      })
      loadClients()
    } catch (error) {
      toast.error('Failed to create client')
      console.error('Client creation error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <BuildingOfficeIcon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Client Management</h2>
            <p className="text-sm text-gray-600">Manage organizations and their projects</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Add Client</span>
        </button>
      </div>

      {/* Clients List */}
      <div className="card">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-12">
            <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No clients</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new client.</p>
            <button
              onClick={() => setShowAddDialog(true)}
              className="mt-4 btn-primary"
            >
              <PlusIcon className="h-5 w-5 inline mr-2" />
              Add First Client
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {clients.map((client) => (
              <div
                key={client.id}
                className="border border-gray-200 rounded-lg p-6 hover:border-blue-300 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">{client.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        client.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {client.status}
                      </span>
                    </div>
                    
                    {client.domain && (
                      <p className="text-sm text-gray-600 mt-1">
                        Domain: <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{client.domain}</span>
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-6 mt-3 text-sm text-gray-600">
                      <div className="flex items-center space-x-1">
                        <FolderIcon className="h-4 w-4" />
                        <span>{client.project_count || 0} projects</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <UsersIcon className="h-4 w-4" />
                        <span>{client.user_count || 0} users</span>
                      </div>
                    </div>
                    
                    {client.contact_email && (
                      <p className="text-sm text-gray-500 mt-2">
                        Contact: {client.contact_name || client.contact_email}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex space-x-2">
                    <button className="btn-secondary text-sm">
                      View Details
                    </button>
                    <button className="btn-secondary text-sm">
                      Manage Projects
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Client Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Add New Client</h3>
            
            <form onSubmit={handleCreateClient} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Client Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full input-field"
                    placeholder="e.g., Acme Corporation"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Domain
                  </label>
                  <input
                    type="text"
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    className="w-full input-field"
                    placeholder="e.g., acme.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry
                  </label>
                  <input
                    type="text"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    className="w-full input-field"
                    placeholder="e.g., Technology"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Name
                  </label>
                  <input
                    type="text"
                    value={formData.contact_name}
                    onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                    className="w-full input-field"
                    placeholder="John Doe"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Email
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    className="w-full input-field"
                    placeholder="contact@acme.com"
                  />
                </div>
                
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full input-field"
                    rows={3}
                    placeholder="Additional notes about this client..."
                  />
                </div>
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
                  Create Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

