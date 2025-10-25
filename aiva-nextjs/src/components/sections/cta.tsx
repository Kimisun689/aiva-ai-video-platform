'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { ArrowRight, Sparkles } from 'lucide-react'

export function CTA() {
  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-r from-aiva-primary/10 via-aiva-accent/10 to-aiva-success/10"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2 mb-8">
            <Sparkles className="w-4 h-4 text-aiva-primary" />
            <span className="text-white/90 text-sm font-medium">
              Ready to get started?
            </span>
          </div>

          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="gradient-text">Start Creating</span>
            <br />
            <span className="text-white">Amazing Videos Today</span>
          </h2>

          <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
            Join thousands of creators who are already using AIVA to produce professional-quality videos with AI.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="xl" variant="aiva" asChild className="group">
              <Link href="/generate">
                Create Your First Video
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
            
            <Button size="xl" variant="glass" asChild>
              <Link href="/auth/register">
                Sign Up Free
              </Link>
            </Button>
          </div>

          <p className="text-sm text-white/60 mt-6">
            No credit card required • Free to start • Cancel anytime
          </p>
        </motion.div>
      </div>

      {/* Floating Elements */}
      <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-aiva-primary/30 rounded-full animate-float"></div>
      <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-aiva-accent/40 rounded-full animate-float" style={{ animationDelay: '1s' }}></div>
      <div className="absolute bottom-1/4 left-3/4 w-1.5 h-1.5 bg-aiva-success/30 rounded-full animate-float" style={{ animationDelay: '2s' }}></div>
    </section>
  )
}
