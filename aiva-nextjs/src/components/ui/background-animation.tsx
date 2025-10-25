'use client'

import { motion } from 'framer-motion'

export function BackgroundAnimation() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-aiva-dark via-aiva-dark-secondary to-aiva-secondary" />
      
      {/* Animated background image */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-20"
        style={{
          backgroundImage: "url('https://vcg03.cfp.cn/creative/vcg/800/new/VCG211469741377.gif')"
        }}
      />
      
      {/* Floating particles */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-2 h-2 bg-aiva-primary/30 rounded-full"
        animate={{
          y: [0, -20, 0],
          opacity: [0.3, 1, 0.3],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      <motion.div
        className="absolute top-3/4 right-1/4 w-1 h-1 bg-aiva-accent/40 rounded-full"
        animate={{
          y: [0, -15, 0],
          opacity: [0.4, 1, 0.4],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1,
        }}
      />
      
      <motion.div
        className="absolute bottom-1/4 left-3/4 w-1.5 h-1.5 bg-aiva-success/30 rounded-full"
        animate={{
          y: [0, -25, 0],
          opacity: [0.3, 1, 0.3],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2,
        }}
      />
      
      <motion.div
        className="absolute top-1/2 right-1/3 w-1 h-1 bg-aiva-warning/30 rounded-full"
        animate={{
          y: [0, -18, 0],
          opacity: [0.3, 1, 0.3],
        }}
        transition={{
          duration: 9,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 0.5,
        }}
      />
    </div>
  )
}
