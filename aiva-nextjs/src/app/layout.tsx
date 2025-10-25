import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AIVA - AI Video Generation Platform',
  description: 'All-in-one AI video creation platform offering video editing, music library, voiceover, and subtitle generation features',
  keywords: ['AI', 'Video Generation', 'Digital Human', 'Video Editing', 'AI Creator'],
  authors: [{ name: 'AIVA Team' }],
  openGraph: {
    title: 'AIVA - AI Video Generation Platform',
    description: 'Create professional-grade video content effortlessly with advanced AI technology',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AIVA - AI Video Generation Platform',
    description: 'Create professional-grade video content effortlessly with advanced AI technology',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-gradient-to-br from-aiva-dark via-aiva-dark-secondary to-aiva-secondary">
            {/* Background particles */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
              <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-aiva-primary/30 rounded-full particle"></div>
              <div className="absolute top-3/4 right-1/4 w-1 h-1 bg-aiva-accent/40 rounded-full particle"></div>
              <div className="absolute bottom-1/4 left-3/4 w-1.5 h-1.5 bg-aiva-success/30 rounded-full particle"></div>
              <div className="absolute top-1/2 right-1/3 w-1 h-1 bg-aiva-warning/30 rounded-full particle"></div>
            </div>
            
            {children}
            <Toaster />
          </div>
        </Providers>
      </body>
    </html>
  )
}
