'use client'

import { motion } from 'framer-motion'
import { Users, Video, Heart, Zap } from 'lucide-react'

const stats = [
  {
    icon: Video,
    value: "1,247",
    label: "Videos Created",
    color: "text-aiva-primary"
  },
  {
    icon: Users,
    value: "856",
    label: "Active Users",
    color: "text-aiva-accent"
  },
  {
    icon: Heart,
    value: "3,421",
    label: "Total Likes",
    color: "text-aiva-success"
  },
  {
    icon: Zap,
    value: "128",
    label: "Today's Posts",
    color: "text-aiva-warning"
  }
]

export function Stats() {
  return (
    <section className="py-20 relative">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="text-center group"
            >
              <div className="aiva-card p-8 hover:scale-105 transition-all duration-300">
                <div className={`w-16 h-16 mx-auto mb-4 rounded-xl bg-gradient-to-r from-white/10 to-white/5 flex items-center justify-center group-hover:shadow-lg transition-all duration-300`}>
                  <stat.icon className={`w-8 h-8 ${stat.color}`} />
                </div>
                <div className="text-4xl font-bold gradient-text mb-2">
                  {stat.value}
                </div>
                <div className="text-white/60 text-sm font-medium">
                  {stat.label}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
