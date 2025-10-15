import { NextRequest, NextResponse } from 'next/server'

const ADMIN_API_URL = process.env.ADMIN_API_URL || 'https://project-agent-admin-api-117860496175.us-central1.run.app'

export async function POST(
  request: NextRequest,
  { params }: { params: { docId: string } }
) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${ADMIN_API_URL}/admin/documents/${params.docId}/assign-category`, {
      method: 'POST',
      headers: {
        'Authorization': request.headers.get('authorization') || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(`Admin API error: ${response.status} - ${errorData.detail || 'Unknown error'}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Assign category API error:', error)
    return NextResponse.json(
      { error: 'Failed to assign document category' },
      { status: 500 }
    )
  }
}
