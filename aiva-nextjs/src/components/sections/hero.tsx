'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Play, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-aiva-dark via-aiva-dark-secondary to-aiva-secondary">
        <div className="absolute inset-0 bg-[url('https://vcg03.cfp.cn/creative/vcg/800/new/VCG211469741377.gif')] bg-cover bg-center opacity-20"></div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2">
              <Sparkles className="w-4 h-4 text-aiva-primary" />
              <span className="text-white/90 text-sm font-medium">
                Powered by Advanced AI Technology
              </span>
            </div>

            {/* Main Heading */}
            <h1 className="text-5xl md:text-7xl font-bold leading-tight">
              <span className="gradient-text">AI Video</span>
              <br />
              <span className="text-white">Creation Platform</span>
            </h1>

            {/* Description */}
            <p className="text-xl md:text-2xl text-white/80 max-w-3xl mx-auto leading-relaxed">
              Create professional-grade video content effortlessly with advanced AI technology. 
              From script to final video, all in one platform.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button size="xl" variant="aiva" asChild className="group">
                <Link href="/generate">
                  Start Creating Now
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              
              <Button size="xl" variant="glass" className="group">
                <Play className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
                Watch Demo
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16 pt-16 border-t border-white/10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text">1M+</div>
                <div className="text-white/60 mt-2">Videos Created</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text">50K+</div>
                <div className="text-white/60 mt-2">Active Users</div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                className="text-center"
              >
                <div className="text-3xl md:text-4xl font-bold gradient-text">99%</div>
                <div className="text-white/60 mt-2">Satisfaction Rate</div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Floating Elements */}
      <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-aiva-primary/30 rounded-full animate-float"></div>
      <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-aiva-accent/40 rounded-full animate-float" style={{ animationDelay: '1s' }}></div>
      <div className="absolute bottom-1/4 left-3/4 w-1.5 h-1.5 bg-aiva-success/30 rounded-full animate-float" style={{ animationDelay: '2s' }}></div>
    </section>
  )
}
