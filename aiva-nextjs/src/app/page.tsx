import { Header } from '@/components/layout/header'
import { Hero } from '@/components/sections/hero'
import { Stats } from '@/components/sections/stats'
import { CTA } from '@/components/sections/cta'
import { Footer } from '@/components/layout/footer'

export default function HomePage() {
  return (
    <main className="relative">
      <Header />
      <Hero />
      <Stats />
      <CTA />
      <Footer />
    </main>
  )
}