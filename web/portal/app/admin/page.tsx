'use client'

import { useState } from 'react'
import { DocumentTextIcon, CloudArrowUpIcon, FolderIcon, CheckCircleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import DocumentInventory from '@/components/admin/DocumentInventory'
import IngestForm from '@/components/admin/IngestForm'
import DriveSync from '@/components/admin/DriveSync'
import DocumentApproval from '@/components/admin/DocumentApproval'

type TabType = 'inventory' | 'ingest' | 'sync' | 'approval' | 'search'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('inventory')

  const tabs = [
    { id: 'inventory', name: 'Inventory', icon: DocumentTextIcon },
    { id: 'ingest', name: 'Ingest Documents', icon: CloudArrowUpIcon },
    { id: 'sync', name: 'Drive Search', icon: FolderIcon },
    { id: 'approval', name: 'Document Approval', icon: CheckCircleIcon },
    { id: 'search', name: 'Search', icon: MagnifyingGlassIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`flex items-center px-1 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'inventory' && <DocumentInventory />}
        {activeTab === 'ingest' && <IngestForm />}
        {activeTab === 'sync' && <DriveSync />}
        {activeTab === 'approval' && <DocumentApproval />}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="card">
              <div className="flex items-center mb-4">
                <div className="p-2 bg-blue-100 rounded-lg mr-3">
                  <MagnifyingGlassIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-lg font-medium text-gray-900">
                    Search Google Drive Documents
                  </h2>
                  <p className="text-sm text-gray-600">
                    Search and discover documents in Google Drive folders
                  </p>
                </div>
              </div>
              
              <div className="text-center py-12">
                <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Search functionality coming soon</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This feature will allow you to search for documents across Google Drive folders.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
