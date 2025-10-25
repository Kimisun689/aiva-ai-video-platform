'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { RegisterForm } from '@/components/auth/register-form'
import { BackgroundAnimation } from '@/components/ui/background-animation'

export default function RegisterPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)

  const handleRegister = async (userData: { 
    username: string; 
    email: string; 
    password: string;
    confirmPassword: string;
  }) => {
    setIsLoading(true)
    try {
      // TODO: Implement actual registration logic
      console.log('Registration attempt:', userData)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Redirect to login page
      router.push('/auth/login')
    } catch (error) {
      console.error('Registration failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <BackgroundAnimation />
      
      <div className="w-full max-w-md relative z-10">
        <RegisterForm 
          onSubmit={handleRegister}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
