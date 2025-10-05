import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import HeaderWrapper from '@/components/HeaderWrapper'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Project Deliverable Agent - Transparent Partners',
  description: 'AI-powered project deliverable search and knowledge management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <HeaderWrapper />
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  )
}
