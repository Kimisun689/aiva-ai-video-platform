'use client'

import { motion } from 'framer-motion'

export function CommunityHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="text-center mb-12"
    >
      <h1 className="text-4xl md:text-5xl font-bold mb-6">
        <span className="gradient-text">Community Hub</span>
      </h1>
      <p className="text-xl text-white/80 max-w-3xl mx-auto">
        Discover amazing AI-generated videos from our creative community. 
        Share your creations and get inspired by others!
      </p>
    </motion.div>
  )
}
