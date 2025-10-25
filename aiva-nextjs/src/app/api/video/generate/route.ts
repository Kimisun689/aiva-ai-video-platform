import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { prompt, style, aspectRatio } = body

    console.log('前端收到请求:', { prompt, style, aspectRatio })
    console.log('后端API URL:', process.env.NEXT_PUBLIC_API_URL)

    // 使用环境变量中的后端API地址
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const apiUrl = `${backendUrl}/api/video/step1`
    
    console.log('调用后端API:', apiUrl)

    // Forward the request to the backend API
    const backendResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        style,
        aspect_ratio: aspectRatio,
      }),
    })

    console.log('后端响应状态:', backendResponse.status)

    const data = await backendResponse.json()
    console.log('后端响应数据:', data)

    if (!backendResponse.ok) {
      return NextResponse.json(
        { success: false, error: data.error || 'Generation failed' },
        { status: backendResponse.status }
      )
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    )
  }
}
