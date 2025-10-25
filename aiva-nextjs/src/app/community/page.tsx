import { Header } from '@/components/layout/header'
import { Footer } from '@/components/layout/footer'
import { CommunityHeader } from '@/components/community/community-header'
import { CommunityStats } from '@/components/community/community-stats'
import { CommunityGrid } from '@/components/community/community-grid'
import { AddPostButton } from '@/components/community/add-post-button'

export default function CommunityPage() {
  return (
    <main className="min-h-screen">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <CommunityHeader />
        <CommunityStats />
        <CommunityGrid />
      </div>
      
      <AddPostButton />
      <Footer />
    </main>
  )
}
