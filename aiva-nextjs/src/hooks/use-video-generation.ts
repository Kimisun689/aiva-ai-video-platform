'use client'

import { useState, useCallback } from 'react'
import { useToast } from '@/hooks/use-toast'

interface GeneratedData {
  script?: string
  shots?: string[]
  characters?: Array<{ name: string; role: string }>
  shotImages?: Array<{ image_url: string; status: string }>
  videos?: Array<{ success: boolean; error?: string }>
  digitalHumanVideos?: Array<{ success: boolean; audio_filename?: string }>
  finalVideo?: string
}

export function useVideoGeneration() {
  const [currentStep, setCurrentStep] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedData, setGeneratedData] = useState<GeneratedData>({})
  const [progress, setProgress] = useState(0)
  const { toast } = useToast()

  const updateProgress = useCallback((step: number) => {
    const progressValue = ((step - 1) / 7) * 100
    setProgress(progressValue)
  }, [])

  const generateVideo = useCallback(async (data: {
    prompt: string
    style: string
    aspectRatio: string
  }) => {
    setIsGenerating(true)
    setCurrentStep(1)
    setProgress(0)
    setGeneratedData({})

    try {
      // Step 1: Script Generation
      setCurrentStep(2)
      updateProgress(2)
      toast({
        title: "正在生成剧本...",
        description: "AI正在创作您的视频剧本",
      })

      const scriptResponse = await fetch('/api/video/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      if (!scriptResponse.ok) {
        throw new Error('剧本生成失败')
      }

      const scriptData = await scriptResponse.json()
      if (!scriptData.success) {
        throw new Error(scriptData.error || '剧本生成失败')
      }
      
      setGeneratedData(prev => ({ ...prev, script: scriptData.script }))
      toast({
        title: "✅ 剧本生成完成",
        description: "开始拆解分镜",
      })

      // Step 2: Storyboard Breakdown
      setCurrentStep(3)
      updateProgress(3)
      toast({
        title: "正在拆解分镜...",
        description: "将剧本拆分为多个镜头",
      })

      const breakdownResponse = await fetch('/api/video/breakdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script: scriptData.script })
      })

      if (!breakdownResponse.ok) {
        throw new Error('分镜拆解失败')
      }

      const breakdownData = await breakdownResponse.json()
      if (!breakdownData.success) {
        throw new Error(breakdownData.error || '分镜拆解失败')
      }

      setGeneratedData(prev => ({ ...prev, shots: breakdownData.shots }))
      toast({
        title: "✅ 分镜拆解完成",
        description: `共生成 ${breakdownData.shots.length} 个镜头`,
      })

      // Step 3: Character Recognition
      setCurrentStep(4)
      updateProgress(4)
      toast({
        title: "正在识别人物...",
        description: "分析剧本中的角色信息",
      })

      const charactersResponse = await fetch('/api/video/characters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script: scriptData.script })
      })

      if (!charactersResponse.ok) {
        throw new Error('人物识别失败')
      }

      const charactersData = await charactersResponse.json()
      if (!charactersData.success) {
        throw new Error(charactersData.error || '人物识别失败')
      }

      setGeneratedData(prev => ({ ...prev, characters: charactersData.characters }))
      toast({
        title: "✅ 人物识别完成",
        description: `识别到 ${charactersData.characters.length} 个角色`,
      })

      // Step 4: Character Images
      setCurrentStep(5)
      updateProgress(5)
      toast({
        title: "正在生成人物图片...",
        description: "为每个角色创建形象",
      })

      const characterImagesResponse = await fetch('/api/video/character-images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!characterImagesResponse.ok) {
        throw new Error('人物图片生成失败')
      }

      const characterImagesData = await characterImagesResponse.json()
      if (!characterImagesData.success) {
        throw new Error(characterImagesData.error || '人物图片生成失败')
      }

      toast({
        title: "✅ 人物图片生成完成",
        description: "开始生成分镜图片",
      })

      // Step 5: Shot Images
      setCurrentStep(6)
      updateProgress(6)
      toast({
        title: "正在生成分镜图片...",
        description: "为每个镜头创建第一帧图片",
      })

      const shotImagesResponse = await fetch('/api/video/shot-images', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!shotImagesResponse.ok) {
        throw new Error('分镜图片生成失败')
      }

      const shotImagesData = await shotImagesResponse.json()
      if (!shotImagesData.success) {
        throw new Error(shotImagesData.error || '分镜图片生成失败')
      }

      // 获取生成的图片
      const shotImagesListResponse = await fetch('/api/video/shot-images', {
        method: 'GET',
      })
      const shotImagesList = await shotImagesListResponse.json()
      setGeneratedData(prev => ({ ...prev, shotImages: shotImagesList.images || [] }))

      toast({
        title: "✅ 分镜图片生成完成",
        description: "开始生成视频片段",
      })

      // Step 6: Video Generation
      setCurrentStep(7)
      updateProgress(7)
      toast({
        title: "正在生成视频片段...",
        description: "这可能需要几分钟时间",
      })

      const videosResponse = await fetch('/api/video/shot-videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!videosResponse.ok) {
        throw new Error('视频生成失败')
      }

      const videosData = await videosResponse.json()
      if (!videosData.success) {
        throw new Error(videosData.error || '视频生成失败')
      }

      setGeneratedData(prev => ({ ...prev, videos: videosData.results || [] }))
      toast({
        title: "✅ 视频片段生成完成",
        description: `成功生成 ${videosData.success_count || 0} 个视频`,
      })

      // Step 7: Digital Human Videos (可选步骤)
      // 如果有对话，生成数字人视频
      if (breakdownData.dialogues && breakdownData.dialogues.length > 0) {
        setCurrentStep(8)
        updateProgress(8)
        toast({
          title: "正在生成数字人视频...",
          description: "为对话创建AI虚拟人",
        })

        const digitalHumanResponse = await fetch('/api/video/digital-human', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })

        if (digitalHumanResponse.ok) {
          const digitalHumanData = await digitalHumanResponse.json()
          if (digitalHumanData.success) {
            setGeneratedData(prev => ({ ...prev, digitalHumanVideos: digitalHumanData.results || [] }))
            toast({
              title: "✅ 数字人视频生成完成",
              description: "开始合并最终视频",
            })
          }
        }
      }

      // Step 8: Final Composition
      setCurrentStep(9)
      updateProgress(9)
      toast({
        title: "正在合成最终视频...",
        description: "将所有片段合并为完整视频",
      })

      const combineResponse = await fetch('/api/video/combine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!combineResponse.ok) {
        throw new Error('视频合并失败')
      }

      const combineData = await combineResponse.json()
      if (!combineData.success) {
        throw new Error(combineData.error || '视频合并失败')
      }

      setGeneratedData(prev => ({ ...prev, finalVideo: combineData.output_file }))

      toast({
        title: "🎉 视频生成完成！",
        description: "您的视频已准备好下载",
      })

    } catch (error) {
      console.error('Generation failed:', error)
      toast({
        title: "生成失败",
        description: error instanceof Error ? error.message : "发生未知错误",
        variant: "destructive"
      })
    } finally {
      setIsGenerating(false)
    }
  }, [toast, updateProgress])

  const resetGeneration = useCallback(() => {
    setCurrentStep(1)
    setIsGenerating(false)
    setGeneratedData({})
    setProgress(0)
  }, [])

  const downloadVideo = useCallback(() => {
    if (generatedData.finalVideo) {
      // TODO: Implement actual download
      window.open('http://localhost:8000/download/combined_video.mp4', '_blank')
    }
  }, [generatedData.finalVideo])

  return {
    currentStep,
    isGenerating,
    generatedData,
    progress,
    generateVideo,
    resetGeneration,
    downloadVideo
  }
}
