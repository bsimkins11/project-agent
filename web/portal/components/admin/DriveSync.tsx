'use client'

import { useState } from 'react'
import { syncGoogleDrive } from '@/lib/api'
import toast from 'react-hot-toast'

export default function DriveSync() {
  const [folderIds, setFolderIds] = useState('')
  const [recursive, setRecursive] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const ids = folderIds.split(',').map(id => id.trim()).filter(Boolean)
    if (ids.length === 0) {
      toast.error('Please enter at least one folder ID')
      return
    }

    setIsLoading(true)
    try {
      const result = await syncGoogleDrive({
        folder_ids: ids,
        recursive
      })
      
      toast.success(`Sync initiated for ${result.folders_processed} folders`)
      setFolderIds('')
    } catch (error) {
      toast.error('Failed to initiate Drive sync')
      console.error('Drive sync error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Google Drive Sync
        </h2>
        
        <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
          <h3 className="font-medium text-yellow-900 mb-2">Setup Required</h3>
          <p className="text-sm text-yellow-700">
            Before using Drive sync, ensure the service account has been granted access to the Drive folders.
            Contact your administrator to share the folders with: sa-ingestor@transparent-agent-test.iam.gserviceaccount.com
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Drive Folder IDs *
            </label>
            <textarea
              value={folderIds}
              onChange={(e) => setFolderIds(e.target.value)}
              className="w-full input-field h-24"
              placeholder="Enter comma-separated Drive folder IDs&#10;Example: 1ABC123def456GHI789, 2XYZ789abc123DEF456"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              You can find folder IDs in the Drive URL: https://drive.google.com/drive/folders/FOLDER_ID_HERE
            </p>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="recursive"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="recursive" className="ml-2 block text-sm text-gray-900">
              Sync subfolders recursively
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary disabled:opacity-50"
          >
            {isLoading ? 'Initiating Sync...' : 'Start Drive Sync'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Sync Status
        </h2>
        <p className="text-gray-600">
          Sync jobs are processed asynchronously. Check the inventory tab to see newly ingested documents.
        </p>
      </div>
    </div>
  )
}
