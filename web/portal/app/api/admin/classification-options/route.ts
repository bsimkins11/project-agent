import { NextRequest, NextResponse } from 'next/server'

const ADMIN_API_URL = process.env.ADMIN_API_URL || 'https://project-agent-admin-api-117860496175.us-central1.run.app'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${ADMIN_API_URL}/admin/classification-options`, {
      method: 'GET',
      headers: {
        'Authorization': request.headers.get('authorization') || '',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Admin API error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Classification options API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch classification options' },
      { status: 500 }
    )
  }
}
