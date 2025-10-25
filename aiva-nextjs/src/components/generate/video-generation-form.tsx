'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Loader2, Wand2 } from 'lucide-react'

interface VideoGenerationFormProps {
  onGenerate: (data: {
    prompt: string
    style: string
    aspectRatio: string
  }) => void
  isGenerating: boolean
}

export function VideoGenerationForm({ onGenerate, isGenerating }: VideoGenerationFormProps) {
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('Realistic')
  const [aspectRatio, setAspectRatio] = useState('16:9')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim()) return
    
    onGenerate({ prompt, style, aspectRatio })
  }

  return (
    <Card className="aiva-card">
      <CardHeader>
        <CardTitle className="text-white flex items-center space-x-2">
          <Wand2 className="w-6 h-6 text-aiva-primary" />
          <span>Start Creating Your Video</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-white font-medium">Video Creative Description</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the video content you want to create, e.g.: A heartwarming story about a little cat learning to ride a bicycle..."
              className="aiva-input min-h-[120px] resize-vertical w-full"
              required
              disabled={isGenerating}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-white font-medium">Video Style</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="aiva-input w-full"
                disabled={isGenerating}
              >
                <option value="Realistic">Realistic</option>
                <option value="Artistic">Artistic</option>
                <option value="Cartoon">Cartoon</option>
                <option value="Cinematic">Cinematic</option>
                <option value="Anime">Anime</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-white font-medium">Aspect Ratio</label>
              <select
                value={aspectRatio}
                onChange={(e) => setAspectRatio(e.target.value)}
                className="aiva-input w-full"
                disabled={isGenerating}
              >
                <option value="16:9">Landscape (16:9)</option>
                <option value="9:16">Portrait (9:16)</option>
                <option value="1:1">Square (1:1)</option>
                <option value="4:3">Standard (4:3)</option>
              </select>
            </div>
          </div>

          <div className="flex gap-4">
            <Button
              type="submit"
              variant="aiva"
              size="lg"
              className="flex-1"
              disabled={isGenerating || !prompt.trim()}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4 mr-2" />
                  Start Video Generation
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
