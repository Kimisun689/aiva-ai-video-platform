'use client'

import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Heart, Share, MessageCircle, Play } from 'lucide-react'

const communityPosts = [
  {
    id: 1,
    user: { name: "Alex Chen", avatar: "A", time: "2 hours ago" },
    title: "Epic Space Adventure",
    description: "Just created this amazing space exploration video using AIVA! The AI really captured the cosmic atmosphere perfectly. 🚀✨",
    likes: 42,
    comments: 8,
    shares: 3
  },
  {
    id: 2,
    user: { name: "Sarah Kim", avatar: "S", time: "5 hours ago" },
    title: "Magical Forest Journey",
    description: "My first attempt with AIVA! Created a beautiful forest scene with magical creatures. The lighting effects are incredible! 🌲✨",
    likes: 67,
    comments: 12,
    shares: 5
  },
  {
    id: 3,
    user: { name: "Mike Johnson", avatar: "M", time: "1 day ago" },
    title: "Cyberpunk City",
    description: "Futuristic cityscape with neon lights and flying cars. AIVA's attention to detail is mind-blowing! 🌃🤖",
    likes: 89,
    comments: 15,
    shares: 8
  },
  {
    id: 4,
    user: { name: "Emma Wilson", avatar: "E", time: "2 days ago" },
    title: "Ocean Depths",
    description: "Underwater exploration with bioluminescent creatures. The color palette is absolutely stunning! 🌊🐠",
    likes: 156,
    comments: 23,
    shares: 12
  },
  {
    id: 5,
    user: { name: "David Lee", avatar: "D", time: "3 days ago" },
    title: "Mountain Sunrise",
    description: "Peaceful mountain landscape at dawn. The way AIVA captured the golden hour lighting is just perfect! ⛰️🌅",
    likes: 203,
    comments: 31,
    shares: 18
  },
  {
    id: 6,
    user: { name: "Lisa Park", avatar: "L", time: "4 days ago" },
    title: "Steampunk Workshop",
    description: "Intricate mechanical workshop with gears and steam. The level of detail in the machinery is incredible! ⚙️🔧",
    likes: 134,
    comments: 19,
    shares: 7
  }
]

export function CommunityGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {communityPosts.map((post, index) => (
        <motion.div
          key={post.id}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: index * 0.1 }}
        >
          <Card className="aiva-card h-full hover:scale-105 transition-all duration-300">
            <CardHeader className="pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-aiva-primary to-aiva-accent rounded-full flex items-center justify-center">
                  <span className="text-white font-bold">{post.user.avatar}</span>
                </div>
                <div>
                  <h4 className="text-white font-semibold text-sm">{post.user.name}</h4>
                  <p className="text-white/60 text-xs">{post.user.time}</p>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div>
                <h3 className="text-white font-semibold text-lg mb-2">{post.title}</h3>
                <p className="text-white/70 text-sm leading-relaxed">{post.description}</p>
              </div>

              {/* Video Preview */}
              <div className="relative bg-gradient-to-r from-aiva-primary/20 to-aiva-accent/20 rounded-lg h-32 flex items-center justify-center border-2 border-dashed border-white/20">
                <div className="text-center">
                  <Play className="w-8 h-8 text-white/40 mx-auto mb-2" />
                  <p className="text-white/60 text-sm">Video Preview</p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center space-x-4">
                  <Button variant="ghost" size="sm" className="text-white/60 hover:text-aiva-primary">
                    <Heart className="w-4 h-4 mr-1" />
                    {post.likes}
                  </Button>
                  <Button variant="ghost" size="sm" className="text-white/60 hover:text-aiva-accent">
                    <MessageCircle className="w-4 h-4 mr-1" />
                    {post.comments}
                  </Button>
                  <Button variant="ghost" size="sm" className="text-white/60 hover:text-aiva-success">
                    <Share className="w-4 h-4 mr-1" />
                    {post.shares}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}
