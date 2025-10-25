'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, Users, Image, Video, Bot } from 'lucide-react'

interface GeneratedData {
  script?: string
  shots?: string[]
  characters?: Array<{ name: string; role: string }>
  shotImages?: Array<{ image_url: string; status: string }>
  videos?: Array<{ success: boolean; error?: string }>
  digitalHumanVideos?: Array<{ success: boolean; audio_filename?: string }>
  finalVideo?: string
}

interface ResultsPanelProps {
  generatedData: GeneratedData
  currentStep: number
}

export function ResultsPanel({ generatedData, currentStep }: ResultsPanelProps) {
  const results = [
    {
      id: 1,
      title: 'Script Generated',
      icon: FileText,
      condition: currentStep >= 2,
      content: generatedData.script ? (
        <div className="space-y-2">
          <p className="text-white/80 text-sm line-clamp-3">{generatedData.script}</p>
          <Badge variant="outline" className="text-xs">Script Ready</Badge>
        </div>
      ) : null
    },
    {
      id: 2,
      title: 'Storyboard Created',
      icon: FileText,
      condition: currentStep >= 3,
      content: generatedData.shots ? (
        <div className="space-y-2">
          <div className="text-white/80 text-sm">
            {generatedData.shots.length} shots created
          </div>
          <Badge variant="outline" className="text-xs">
            {generatedData.shots.length} Shots
          </Badge>
        </div>
      ) : null
    },
    {
      id: 3,
      title: 'Characters Identified',
      icon: Users,
      condition: currentStep >= 4,
      content: generatedData.characters ? (
        <div className="space-y-2">
          <div className="text-white/80 text-sm">
            {generatedData.characters.length} characters found
          </div>
          <div className="flex flex-wrap gap-1">
            {generatedData.characters.slice(0, 3).map((char, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {char.name}
              </Badge>
            ))}
            {generatedData.characters.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{generatedData.characters.length - 3}
              </Badge>
            )}
          </div>
        </div>
      ) : null
    },
    {
      id: 4,
      title: 'Images Generated',
      icon: Image,
      condition: currentStep >= 6,
      content: generatedData.shotImages ? (
        <div className="space-y-2">
          <div className="text-white/80 text-sm">
            {generatedData.shotImages.filter(img => img.status === 'success').length} images ready
          </div>
          <Badge variant="outline" className="text-xs">
            {generatedData.shotImages.length} Total
          </Badge>
        </div>
      ) : null
    },
    {
      id: 5,
      title: 'Videos Generated',
      icon: Video,
      condition: currentStep >= 7,
      content: generatedData.videos ? (
        <div className="space-y-2">
          <div className="text-white/80 text-sm">
            {generatedData.videos.filter(v => v.success).length} videos ready
          </div>
          <Badge variant="outline" className="text-xs">
            {generatedData.videos.length} Total
          </Badge>
        </div>
      ) : null
    },
    {
      id: 6,
      title: 'Digital Human Videos',
      icon: Bot,
      condition: currentStep >= 8,
      content: generatedData.digitalHumanVideos ? (
        <div className="space-y-2">
          <div className="text-white/80 text-sm">
            {generatedData.digitalHumanVideos.filter(v => v.success).length} digital human videos
          </div>
          <Badge variant="outline" className="text-xs">
            AI Generated
          </Badge>
        </div>
      ) : null
    }
  ]

  const hasResults = results.some(result => result.condition && result.content)

  return (
    <Card className="aiva-card">
      <CardHeader>
        <CardTitle className="text-white flex items-center space-x-2">
          <div className="w-6 h-6 bg-gradient-to-r from-aiva-primary to-aiva-accent rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">📋</span>
          </div>
          <span>Generation Results</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!hasResults ? (
          <div className="text-center py-8">
            <div className="text-white/60 text-sm">
              Waiting to start...
            </div>
            <div className="text-white/40 text-xs mt-2">
              Please fill in your video creative description and click the generate button to start creating
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {results.map((result) => (
              result.condition && result.content && (
                <div key={result.id} className="flex items-start space-x-3 p-3 rounded-lg bg-white/5 border border-white/10">
                  <result.icon className="w-5 h-5 text-aiva-primary mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-medium text-sm mb-1">
                      {result.title}
                    </div>
                    {result.content}
                  </div>
                </div>
              )
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
