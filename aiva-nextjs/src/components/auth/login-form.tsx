'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { User, Lock, ArrowLeft, Loader2 } from 'lucide-react'

interface LoginFormProps {
  onSubmit: (credentials: { username: string; password: string }) => void
  isLoading: boolean
}

export function LoginForm({ onSubmit, isLoading }: LoginFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <Card className="w-full max-w-md mx-auto aiva-card">
      <CardHeader className="text-center">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <div className="w-12 h-12 rounded-lg overflow-hidden">
            <img 
              src="/icon-logo.jpeg" 
              alt="AIVA Logo" 
              className="w-full h-full object-cover"
            />
          </div>
          <span className="text-2xl font-bold gradient-text">AIVA</span>
        </div>
        <CardTitle className="text-2xl text-white">Welcome Back</CardTitle>
        <p className="text-white/60 text-sm">Sign in to your account to continue creating amazing videos</p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-white/80 text-sm font-medium">Email or Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Enter your email or username"
                className="aiva-input pl-10"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-white/80 text-sm font-medium">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                className="aiva-input pl-10"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="aiva"
            size="lg"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-white/60 text-sm">
            Don't have an account?{' '}
            <Link href="/auth/register" className="text-aiva-primary hover:text-aiva-accent transition-colors">
              Sign up
            </Link>
          </p>
        </div>

        <div className="mt-6">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-white/60 hover:text-white"
            asChild
          >
            <Link href="/">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Homepage
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
