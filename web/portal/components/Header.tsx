'use client'

import { useState, useEffect } from 'react'

interface HeaderProps {
  title?: string
  subtitle?: string
  showDocumentsDropdown?: boolean
  showAdminLink?: boolean
  showSignOut?: boolean
  isAdminPage?: boolean
}

export default function Header({ 
  title,
  subtitle,
  showDocumentsDropdown = true,
  showAdminLink = true,
  showSignOut = true,
  isAdminPage = false
}: HeaderProps) {
  // Set default titles based on page type
  const defaultTitle = isAdminPage ? "Project Deliverable Agent Admin" : "Project Deliverable Agent"
  const defaultSubtitle = isAdminPage ? "Transparent Partners" : "AI-Powered Project Deliverable Knowledge Assistant"
  
  const finalTitle = title || defaultTitle
  const finalSubtitle = subtitle || defaultSubtitle
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [email, setEmail] = useState('')
  const [isHydrated, setIsHydrated] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [projects, setProjects] = useState<Array<{id: string, name: string}>>([])
  const [showProjectSelector, setShowProjectSelector] = useState(false)

  useEffect(() => {
    // Mark as hydrated to avoid SSR issues
    setIsHydrated(true)
    
    // Check authentication state
    const savedAuth = localStorage.getItem('isAuthenticated')
    const savedEmail = localStorage.getItem('userEmail')
    const authToken = localStorage.getItem('auth_token')
    
    // Consider authenticated if either the main auth or admin auth token exists
    if ((savedAuth === 'true' && savedEmail) || authToken) {
      setIsAuthenticated(true)
      setEmail(savedEmail || 'admin@transparent.partners')
      
      // Load projects for project selector
      loadProjects()
    }
    
    // Check for saved project selection
    const savedProject = localStorage.getItem('selected_project_id')
    if (savedProject) {
      setSelectedProject(savedProject)
    }
  }, [])
  
  const loadProjects = async () => {
    try {
      const response = await fetch('/api/admin/rbac/projects')
      if (response.ok) {
        const data = await response.json()
        setProjects(data.projects || [])
        setShowProjectSelector(data.projects && data.projects.length > 0)
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }
  
  const handleProjectChange = (projectId: string) => {
    setSelectedProject(projectId)
    localStorage.setItem('selected_project_id', projectId)
    // Trigger page reload or event to update document list
    window.dispatchEvent(new CustomEvent('projectChanged', { detail: { projectId } }))
  }

  const handleSignOut = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('auth_token')
    window.location.href = '/'
  }

  // Don't render until hydrated to avoid SSR issues
  if (!isHydrated) {
    return null
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <a href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <img 
                src="/transparent-partners-logo.png" 
                alt="Transparent Partners" 
                className="h-8 w-auto"
              />
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {finalTitle}
                </h1>
                <p className="text-xs text-gray-500">
                  {finalSubtitle}
                </p>
              </div>
            </a>
          </div>
          <nav className="flex items-center space-x-6">
            {/* Project Selector (shown when projects exist) */}
            {showProjectSelector && projects.length > 0 && (
              <div className="relative">
                <label className="text-xs text-gray-500 block mb-1">Project</label>
                <select
                  value={selectedProject}
                  onChange={(e) => handleProjectChange(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-3 py-1.5 bg-white text-gray-700 hover:border-gray-400 transition-colors"
                >
                  <option value="">All Projects</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          
            {/* Home Link (shown on admin page) */}
            {isAdminPage && (
              <a 
                href="/" 
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Home
              </a>
            )}

            {/* Documents Dropdown */}
            {showDocumentsDropdown && (
              <div className="relative group">
                <button className="text-sm text-gray-600 hover:text-gray-900 transition-colors flex items-center space-x-1">
                  <span>Documents</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {/* Dropdown Menu */}
                <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <a 
                      href="/documents/sow" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      SOW
                    </a>
                    <a 
                      href="/documents/timeline" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Timeline
                    </a>
                    <a 
                      href="/documents/deliverables" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Deliverables
                    </a>
                    <a 
                      href="/documents/misc" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Misc
                    </a>
                  </div>
                </div>
              </div>
            )}

            {showAdminLink && (
              <a 
                href="/admin" 
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Admin
              </a>
            )}
            
            {showSignOut && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>Demo Mode</span>
                <button 
                  onClick={handleSignOut}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Sign Out
                </button>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}
