'use client'

import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

export function AddPostButton() {
  const handleAddPost = () => {
    // TODO: Implement add post functionality
    alert('Add Post feature coming soon! 🚀')
  }

  return (
    <Button
      size="icon"
      variant="aiva"
      onClick={handleAddPost}
      className="fixed bottom-8 right-8 w-14 h-14 rounded-full shadow-lg hover:scale-110 transition-transform z-50"
      title="Add New Post"
    >
      <Plus className="w-6 h-6" />
    </Button>
  )
}
