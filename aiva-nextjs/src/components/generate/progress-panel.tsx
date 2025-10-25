'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CheckCircle, Circle, Loader2 } from 'lucide-react'

interface ProgressPanelProps {
  currentStep: number
  progress: number
  isGenerating: boolean
}

const steps = [
  { id: 1, name: 'Creative Input', description: 'Processing your prompt' },
  { id: 2, name: 'Script Generation', description: 'Generating video script' },
  { id: 3, name: 'Storyboard Breakdown', description: 'Creating storyboard' },
  { id: 4, name: 'Character Recognition', description: 'Identifying characters' },
  { id: 5, name: 'Character Images', description: 'Generating character images' },
  { id: 6, name: 'Shot Images', description: 'Creating shot visuals' },
  { id: 7, name: 'Digital Human', description: 'Generating digital human videos' },
  { id: 8, name: 'Final Composition', description: 'Combining final video' },
]

export function ProgressPanel({ currentStep, progress, isGenerating }: ProgressPanelProps) {
  return (
    <Card className="aiva-card">
      <CardHeader>
        <CardTitle className="text-white flex items-center space-x-2">
          <div className="w-6 h-6 bg-gradient-to-r from-aiva-primary to-aiva-accent rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">📊</span>
          </div>
          <span>Generation Progress</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-white/80">Overall Progress</span>
            <span className="text-aiva-primary font-medium">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {steps.map((step) => (
            <div key={step.id} className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {step.id < currentStep ? (
                  <CheckCircle className="w-5 h-5 text-aiva-success" />
                ) : step.id === currentStep && isGenerating ? (
                  <Loader2 className="w-5 h-5 text-aiva-primary animate-spin" />
                ) : (
                  <Circle className="w-5 h-5 text-white/40" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-medium ${
                  step.id <= currentStep ? 'text-white' : 'text-white/60'
                }`}>
                  {step.name}
                </div>
                <div className="text-xs text-white/50">
                  {step.description}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Status */}
        <div className="pt-4 border-t border-white/10">
          <div className="text-sm text-white/80">
            {isGenerating ? (
              <span className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating video...</span>
              </span>
            ) : currentStep === 8 ? (
              <span className="text-aiva-success">✅ Generation complete!</span>
            ) : (
              <span>Ready to start</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
