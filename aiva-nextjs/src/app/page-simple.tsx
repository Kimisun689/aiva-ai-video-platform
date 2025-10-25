import { Header } from '@/components/layout/header'

export default function SimpleHomePage() {
  return (
    <main className="relative">
      <Header />
      <div className="pt-16 min-h-screen bg-gradient-to-br from-aiva-dark via-aiva-dark-secondary to-aiva-secondary">
        <div className="container mx-auto px-4 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-aiva-primary to-aiva-accent bg-clip-text text-transparent">
                AIVA
              </span>
            </h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              AI Video Generation Platform
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
