'use client'

import { usePathname } from 'next/navigation'
import Header from './Header'

export default function HeaderWrapper() {
  const pathname = usePathname()
  const isAdminPage = pathname?.startsWith('/admin')
  
  
  return (
    <Header 
      isAdminPage={isAdminPage}
      showDocumentsDropdown={!isAdminPage}
      showAdminLink={!isAdminPage}
    />
  )
}
