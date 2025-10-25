'use client'

import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Video, Users, Heart, Zap } from 'lucide-react'

const stats = [
  { icon: Video, value: "1,247", label: "Videos Created", color: "text-aiva-primary" },
  { icon: Users, value: "856", label: "Active Users", color: "text-aiva-accent" },
  { icon: Heart, value: "3,421", label: "Total Likes", color: "text-aiva-success" },
  { icon: Zap, value: "128", label: "Today's Posts", color: "text-aiva-warning" }
]

export function CommunityStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: index * 0.1 }}
        >
          <Card className="aiva-card text-center hover:scale-105 transition-all duration-300">
            <CardContent className="p-6">
              <div className={`w-12 h-12 mx-auto mb-4 rounded-xl bg-gradient-to-r from-white/10 to-white/5 flex items-center justify-center`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="text-3xl font-bold gradient-text mb-2">
                {stat.value}
              </div>
              <div className="text-white/60 text-sm">
                {stat.label}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}
