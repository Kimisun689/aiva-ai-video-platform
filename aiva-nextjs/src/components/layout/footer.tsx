import Link from 'next/link'
import { Github, Twitter, Mail, Heart } from 'lucide-react'

export function Footer() {
  return (
    <footer className="bg-aiva-dark-secondary/50 border-t border-white/10 mt-20">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg overflow-hidden">
                <img 
                  src="/icon-logo.jpeg" 
                  alt="AIVA Logo" 
                  className="w-full h-full object-cover"
                />
              </div>
              <span className="text-xl font-bold gradient-text">AIVA</span>
            </div>
            <p className="text-white/60 text-sm">
              Create professional-grade video content effortlessly with advanced AI technology.
            </p>
            <div className="flex space-x-4">
              <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                <Twitter className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                <Github className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                <Mail className="w-5 h-5" />
              </Link>
            </div>
          </div>

          {/* Product */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Product</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/generate" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Video Generation
                </Link>
              </li>
              <li>
                <Link href="/community" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Community
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  API Documentation
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Support</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Help Center
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Status
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Bug Reports
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div className="space-y-4">
            <h3 className="text-white font-semibold">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  Cookie Policy
                </Link>
              </li>
              <li>
                <Link href="#" className="text-white/60 hover:text-aiva-primary transition-colors">
                  GDPR
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-white/60 text-sm">
            © 2024 AIVA. All rights reserved.
          </p>
          <p className="text-white/60 text-sm flex items-center mt-4 md:mt-0">
            Made with <Heart className="w-4 h-4 mx-1 text-aiva-primary" /> by the AIVA team
          </p>
        </div>
      </div>
    </footer>
  )
}
