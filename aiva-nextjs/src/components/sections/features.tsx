'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Video, Music, Mic, ClosedCaptioning, ArrowRight } from 'lucide-react'

const features = [
  {
    icon: Video,
    title: "Intelligent Video Editing",
    description: "Revolutionary AI video editing technology supports smart clipping, automatic transitions, and scene recognition. Through deep learning algorithms, it automatically optimizes video color, stabilizes footage, and removes noise.",
    gradient: "from-red-500 to-pink-500",
    action: "Try Now"
  },
  {
    icon: Music,
    title: "Massive Music Library",
    description: "With over 1 million licensed music tracks covering various genres including pop, classical, electronic, and rock. The intelligent scoring system automatically recommends the best background music.",
    gradient: "from-teal-500 to-cyan-500",
    action: "Explore Music"
  },
  {
    icon: Mic,
    title: "AI Voice Synthesis",
    description: "Utilizing the most advanced neural network voice synthesis technology, offering over 200 natural and smooth voice styles, supporting more than 50 languages including Chinese, English, Japanese, and Korean.",
    gradient: "from-yellow-500 to-orange-500",
    action: "Listen to Demo"
  },
  {
    icon: ClosedCaptioning,
    title: "Smart Subtitle Generation",
    description: "Based on deep learning speech recognition technology, accurately identifies dialogue content in videos and automatically generates multilingual subtitles. Supports subtitle style customization.",
    gradient: "from-blue-500 to-indigo-500",
    action: "Generate Subtitles"
  }
]

export function Features() {
  return (
    <section className="py-20 relative">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="gradient-text">Powerful Features</span>
          </h2>
          <p className="text-xl text-white/80 max-w-3xl mx-auto">
            Everything you need to create professional video content with AI
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              <Card className="aiva-card h-full group hover:scale-105 transition-all duration-300">
                <CardHeader className="text-center">
                  <div className={`w-16 h-16 mx-auto mb-4 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center`}>
                    {React.createElement(feature.icon, { className: "w-8 h-8 text-white" })}
                  </div>
                  <CardTitle className="text-white text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <CardDescription className="text-white/70 text-sm leading-relaxed">
                    {feature.description}
                  </CardDescription>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full group-hover:bg-white group-hover:text-aiva-dark transition-colors"
                  >
                    {feature.action}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
