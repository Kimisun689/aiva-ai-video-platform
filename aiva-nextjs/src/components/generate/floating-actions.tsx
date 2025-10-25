'use client'

import { Button } from '@/components/ui/button'
import { Download, RotateCcw } from 'lucide-react'

interface FloatingActionsProps {
  onReset: () => void
  onDownload: () => void
  isGenerating: boolean
  hasVideo: boolean
}

export function FloatingActions({ onReset, onDownload, isGenerating, hasVideo }: FloatingActionsProps) {
  return (
    <div className="fixed bottom-8 right-8 flex flex-col space-y-4 z-50">
      {hasVideo && (
        <Button
          size="icon"
          variant="aiva"
          onClick={onDownload}
          className="w-14 h-14 rounded-full shadow-lg hover:scale-110 transition-transform"
          title="Download Video"
        >
          <Download className="w-6 h-6" />
        </Button>
      )}
      
      <Button
        size="icon"
        variant="glass"
        onClick={onReset}
        disabled={isGenerating}
        className="w-14 h-14 rounded-full shadow-lg hover:scale-110 transition-transform"
        title="Restart Generation"
      >
        <RotateCcw className="w-6 h-6" />
      </Button>
    </div>
  )
}
