'use client'

import { useState } from 'react'
import { ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import apiClient from '@/lib/api-client'

export default function RBACMigration() {
  const [migrating, setMigrating] = useState(false)
  const [migrationResult, setMigrationResult] = useState<{
    migrated: number
    skipped: number
    client_id: string
    project_id: string
  } | null>(null)

  const handleMigrate = async () => {
    if (!confirm('This will migrate all existing documents to the default client and project. Continue?')) {
      return
    }

    setMigrating(true)
    try {
      const response = await apiClient.post<{
        success: boolean
        migrated: number
        skipped: number
        client_id: string
        project_id: string
        message: string
      }>(
        '/api/admin/migrate-to-rbac',
        {
          client_id: 'client-transparent-partners',
          project_id: 'project-chr-martech'
        }
      )
      
      setMigrationResult(response)
      toast.success(response.message)
    } catch (error) {
      toast.error('Migration failed')
      console.error('Migration error:', error)
    } finally {
      setMigrating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-purple-100 rounded-lg">
          <ArrowPathIcon className="h-6 w-6 text-purple-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">RBAC Migration</h2>
          <p className="text-sm text-gray-600">One-time migration to multi-tenant structure</p>
        </div>
      </div>

      {/* Migration Card */}
      <div className="card">
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">📋 What This Does:</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Assigns all existing documents to <span className="font-mono bg-blue-100 px-1">client-transparent-partners</span></li>
              <li>• Assigns all existing documents to <span className="font-mono bg-blue-100 px-1">project-chr-martech</span></li>
              <li>• Sets visibility to "project" for all documents</li>
              <li>• Updates project document count</li>
              <li>• Skips documents already migrated (safe to run multiple times)</li>
            </ul>
          </div>

          {!migrationResult ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-900 mb-1">⚠️ Before You Migrate:</h4>
                  <ul className="text-sm text-yellow-800 space-y-1">
                    <li>• Ensure default client and project exist in Firestore</li>
                    <li>• This is a one-time operation (safe to run multiple times)</li>
                    <li>• All existing documents will be accessible under the default project</li>
                    <li>• You can create additional projects later and move documents</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <CheckCircleIcon className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-green-900 mb-2">✅ Migration Complete!</h4>
                  <div className="text-sm text-green-800 space-y-1">
                    <p>• Migrated: <span className="font-bold">{migrationResult.migrated}</span> documents</p>
                    <p>• Skipped: <span className="font-bold">{migrationResult.skipped}</span> (already migrated)</p>
                    <p>• Client: <span className="font-mono bg-green-100 px-1">{migrationResult.client_id}</span></p>
                    <p>• Project: <span className="font-mono bg-green-100 px-1">{migrationResult.project_id}</span></p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleMigrate}
            disabled={migrating}
            className="w-full btn-primary flex items-center justify-center space-x-2"
          >
            {migrating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Migrating Documents...</span>
              </>
            ) : (
              <>
                <ArrowPathIcon className="h-5 w-5" />
                <span>{migrationResult ? 'Run Migration Again' : 'Start Migration'}</span>
              </>
            )}
          </button>
          
          {migrationResult && (
            <p className="text-xs text-center text-gray-500">
              You can run this again to migrate any new documents that haven't been assigned to a project yet.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

