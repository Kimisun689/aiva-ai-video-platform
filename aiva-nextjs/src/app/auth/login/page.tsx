'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { LoginForm } from '@/components/auth/login-form'
import { BackgroundAnimation } from '@/components/ui/background-animation'

export default function LoginPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (credentials: { username: string; password: string }) => {
    setIsLoading(true)
    try {
      // TODO: Implement actual login logic
      console.log('Login attempt:', credentials)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Redirect to home page
      router.push('/')
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <BackgroundAnimation />
      
      <div className="w-full max-w-md relative z-10">
        <LoginForm 
          onSubmit={handleLogin}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
