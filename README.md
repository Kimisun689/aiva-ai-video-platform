# 🎬 AIVA - AI Video Platform

> All-in-one AI-powered video generation platform

AIVA is a comprehensive AI video generation platform that enables users to create professional videos from text prompts using advanced AI technologies. The platform combines script breakdown, character generation, scene creation, and video synthesis into a seamless workflow.

## ✨ Features

- **🤖 AI Script Breakdown**: Automatically analyze and break down scripts into scenes and dialogues
- **👤 Character Generation**: Create consistent character images using AI image generation
- **🎨 Scene Creation**: Generate scene-specific images and backgrounds
- **🎥 Video Synthesis**: Combine characters, scenes, and dialogues into complete videos
- **💬 Digital Human**: AI-powered digital human video generation with natural speech
- **🌐 Community Platform**: Share and discover AI-generated videos
- **🔐 User Authentication**: Secure login and registration system

## 🏗️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Lucide Icons** - Modern icon library

### Backend
- **Python FastAPI** - High-performance API framework
- **SQLite** - Lightweight database
- **Alibaba Cloud APIs** - AI video and image generation services
- **Dashscope** - AI model integration

## 📁 Project Structure

```
aiva-ai-video-platform/
├── aiva-nextjs/          # Next.js frontend application
│   ├── src/
│   │   ├── app/          # App router pages
│   │   ├── components/   # React components
│   │   └── hooks/        # Custom hooks
│   └── public/           # Static assets
├── Back-end/             # Python backend API
│   ├── main.py           # FastAPI main application
│   ├── video_gnt.py      # Video generation logic
│   ├── image_generator.py # Image generation service
│   └── requirements.txt  # Python dependencies
└── Front-end/            # Legacy HTML frontend
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Alibaba Cloud account with API access

### Frontend Setup

```bash
cd aiva-nextjs
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

```bash
cd Back-end
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend API will be available at `http://localhost:8000`

### Environment Variables

Create a `.env.local` file in the `aiva-nextjs` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Configure your Alibaba Cloud credentials in the backend configuration files.

## 📖 API Documentation

The backend provides comprehensive API documentation. Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

See [API_DOCUMENTATION.md](Back-end/API_DOCUMENTATION.md) for detailed API information.

## 🎯 Usage

1. **Register/Login**: Create an account or log in to the platform
2. **Generate Video**: 
   - Enter your video script or prompt
   - Configure generation parameters
   - Click "Generate" to start the AI video creation process
3. **Monitor Progress**: Track the generation progress in real-time
4. **View Results**: Preview and download your generated video
5. **Share**: Publish your video to the community platform

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

### Contributors

- [@Kimisun689](https://github.com/Kimisun689)
- [@allen546](https://github.com/allen546)
- [@Unknownuserfrommars](https://github.com/Unknownuserfrommars)

## 📝 License

This project is licensed under the MIT License.

## 🔗 Links

- **Repository**: [https://github.com/Kimisun689/aiva-ai-video-platform](https://github.com/Kimisun689/aiva-ai-video-platform)
- **Issues**: [https://github.com/Kimisun689/aiva-ai-video-platform/issues](https://github.com/Kimisun689/aiva-ai-video-platform/issues)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ by the AIVA Team
