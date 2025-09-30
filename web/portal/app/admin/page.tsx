'use client'

import { useState } from 'react'
import { DocumentTextIcon, CloudArrowUpIcon, FolderIcon } from '@heroicons/react/24/outline'
import DocumentInventory from '@/components/admin/DocumentInventory'
import IngestForm from '@/components/admin/IngestForm'
import DriveSync from '@/components/admin/DriveSync'

type TabType = 'inventory' | 'ingest' | 'sync'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('inventory')

  const tabs = [
    { id: 'inventory', name: 'Inventory', icon: DocumentTextIcon },
    { id: 'ingest', name: 'Ingest Documents', icon: CloudArrowUpIcon },
    { id: 'sync', name: 'Drive Sync', icon: FolderIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Project Agent Admin
              </h1>
              <span className="ml-2 text-sm text-gray-500">
                Transparent Partners
              </span>
            </div>
            <nav className="flex space-x-8">
              <a href="/" className="text-gray-600 hover:text-gray-900">
                Search
              </a>
            </nav>
          </div>
        </div>
      </header>

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
      </main>
    </div>
  )
}
