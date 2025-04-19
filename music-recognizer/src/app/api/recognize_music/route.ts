import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const response = await fetch('http://localhost:8000/recognize_snippet', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fake: true }),
    })

    const data = await response.json()
    return NextResponse.json(data)

  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}