# AIVA - AI Video Generation Platform (Next.js)

A modern, responsive web application built with Next.js 15 and the App Router for AI-powered video generation. This is a complete redesign of the original AIVA platform using modern web technologies.

## 🚀 Features

- **Modern UI/UX**: Built with Tailwind CSS and Framer Motion for smooth animations
- **App Router**: Uses Next.js 15's latest App Router for optimal performance
- **TypeScript**: Fully typed for better development experience
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Progress**: Live updates during video generation process
- **Community Hub**: Share and discover AI-generated videos
- **Authentication**: Secure login and registration system

## 🛠️ Tech Stack

- **Framework**: Next.js 15.5.4 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Animations**: Framer Motion
- **UI Components**: Radix UI primitives with custom styling
- **Icons**: Lucide React
- **State Management**: React Hooks + Zustand (for complex state)
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form with Zod validation

## 📁 Project Structure

```
aiva-nextjs/
├── src/
│   ├── app/                    # App Router pages
│   │   ├── (auth)/            # Authentication routes
│   │   ├── api/               # API routes
│   │   ├── community/         # Community page
│   │   ├── generate/          # Video generation page
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/            # React components
│   │   ├── auth/              # Authentication components
│   │   ├── community/         # Community components
│   │   ├── generate/          # Video generation components
│   │   ├── layout/            # Layout components
│   │   ├── sections/          # Home page sections
│   │   └── ui/                # Reusable UI components
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility functions
│   └── types/                 # TypeScript type definitions
├── public/                    # Static assets
├── next.config.mjs           # Next.js configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── package.json              # Dependencies and scripts
```

## 🎨 Design System

### Colors
- **Primary**: #FF6B35 (Orange)
- **Secondary**: #1f3857 (Dark Blue)
- **Accent**: #4ECDC4 (Teal)
- **Success**: #45B7D1 (Blue)
- **Warning**: #FFA726 (Amber)
- **Dark**: #0f0f23 (Very Dark Blue)

### Typography
- **Font Family**: Inter, PingFang SC, Segoe UI, system-ui
- **Headings**: Bold, gradient text effects
- **Body**: Regular weight, high contrast for readability

### Components
- **Cards**: Glass morphism effect with backdrop blur
- **Buttons**: Gradient backgrounds with hover animations
- **Inputs**: Dark theme with focus states
- **Progress**: Animated progress bars with gradients

## 🚀 Getting Started

### Prerequisites
- Node.js 18.17 or later
- npm, yarn, or pnpm

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aiva-nextjs
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` with your configuration:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXTAUTH_SECRET=your-secret-key
   NEXTAUTH_URL=http://localhost:3000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📱 Pages & Features

### Home Page (`/`)
- Hero section with animated background
- Feature showcase with interactive cards
- Statistics display
- Call-to-action sections

### Video Generation (`/generate`)
- Multi-step video generation process
- Real-time progress tracking
- Results preview and management
- Download functionality

### Community (`/community`)
- User-generated content grid
- Interactive post cards
- Statistics dashboard
- Social features (likes, comments, shares)

### Authentication (`/auth/login`, `/auth/register`)
- Modern login/register forms
- Form validation with error handling
- Responsive design
- Secure authentication flow

## 🔧 API Integration

The application integrates with the existing AIVA backend API:

- **Video Generation**: `/api/video/generate`
- **Authentication**: `/api/auth/login`, `/api/auth/register`
- **File Downloads**: `/api/download/`

API routes are configured to proxy requests to the backend server running on `localhost:8000`.

## 🎯 Key Improvements Over Original

1. **Modern Architecture**: Next.js 15 with App Router for better performance
2. **Type Safety**: Full TypeScript implementation
3. **Responsive Design**: Mobile-first approach with Tailwind CSS
4. **Better UX**: Smooth animations and loading states
5. **Component Reusability**: Modular component architecture
6. **SEO Optimization**: Proper meta tags and structured data
7. **Performance**: Optimized images and code splitting
8. **Accessibility**: ARIA labels and keyboard navigation

## 🚀 Deployment

### Vercel (Recommended)
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Configure environment variables
4. Deploy automatically

### Other Platforms
The app can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- DigitalOcean App Platform

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Next.js team for the amazing framework
- Tailwind CSS for the utility-first CSS framework
- Radix UI for accessible component primitives
- Framer Motion for smooth animations
- Lucide for beautiful icons

---

**Built with ❤️ by the AIVA Team**
