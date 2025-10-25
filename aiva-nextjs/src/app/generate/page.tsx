'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { VideoGenerationForm } from '@/components/generate/video-generation-form'
import { ProgressPanel } from '@/components/generate/progress-panel'
import { ResultsPanel } from '@/components/generate/results-panel'
import { FloatingActions } from '@/components/generate/floating-actions'
import { useVideoGeneration } from '@/hooks/use-video-generation'

export default function GeneratePage() {
  const {
    currentStep,
    isGenerating,
    generatedData,
    progress,
    generateVideo,
    resetGeneration,
    downloadVideo
  } = useVideoGeneration()

  return (
    <main className="min-h-screen">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Generation Area */}
          <div className="lg:col-span-2 space-y-6">
            <VideoGenerationForm 
              onGenerate={generateVideo}
              isGenerating={isGenerating}
            />
            
            <ResultsPanel 
              generatedData={generatedData}
              currentStep={currentStep}
            />
          </div>
          
          {/* Sidebar */}
          <div className="space-y-6">
            <ProgressPanel 
              currentStep={currentStep}
              progress={progress}
              isGenerating={isGenerating}
            />
          </div>
        </div>
      </div>
      
      <FloatingActions 
        onReset={resetGeneration}
        onDownload={downloadVideo}
        isGenerating={isGenerating}
        hasVideo={generatedData.finalVideo}
      />
    </main>
  )
}
