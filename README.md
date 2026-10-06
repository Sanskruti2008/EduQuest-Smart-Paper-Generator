# EduQuest.ai - AI-Powered Question Paper Generator

Generate professional question papers automatically using AI or build them manually with an intuitive drag-and-drop interface.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ installed
- Python 3.8+ installed
- npm or yarn package manager

### Installation

1. **Install Frontend Dependencies:**
```bash
npm install
```

2. **Setup Python Backend:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Start Backend Server:**
```bash
cd backend
python server.py
```
*Backend runs on http://localhost:5000*

4. **Start Frontend (in new terminal):**
```bash
npm run dev
```
*Frontend runs on http://localhost:5173*

## 📖 Documentation

- [Backend Setup Guide](docs/BACKEND_SETUP.md)
- [Hero Component Details](docs/HERO_COMPONENT.md)

## 📦 Tech Stack

**Frontend:**
- React 18.3 with TypeScript
- Vite 5 - Build tool
- Tailwind CSS 3.4
- Framer Motion - Animations
- React Router 6 - Routing

**Backend:**
- Flask - Python web framework
- Groq AI - Question generation

## 🗂️ Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Header.jsx
│   └── ProgressIndicator.jsx
├── context/            # React Context for question-bank and review state
├── pages/              # Dashboard, question-bank, syllabus, OCR, and review pages
├── App.jsx            # Main app component with routing
├── main.jsx           # Application entry point
└── index.css          # Tailwind CSS imports and custom styles
```

## 🎯 Features

- **Question Bank** - Browse and search available questions
- **OCR Upload** - Extract and review questions from uploaded papers
- **Syllabus and RUA Analysis** - Inspect syllabus coverage and learning outcomes
- **Faculty and moderation dashboards** - Manage review workflows and faculty data
- **Quality Checks** - Built-in validation for marks, difficulty, and structure
- **Multiple Export Formats** - PDF and DOCX export options
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

## 🛠️ Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## 🎨 Customization

### Tailwind Configuration
Edit `tailwind.config.js` to customize colors, spacing, and other design tokens:

```js
theme: {
  extend: {
    colors: {
      primary: {
        DEFAULT: '#4A90E2',
        dark: '#357ABD',
        light: '#E8F4FD',
      },
      // ... more colors
    },
  },
}
```

### Global Styles
Custom component styles are defined in `src/index.css` using Tailwind's `@layer components` directive.

## 📄 License

MIT

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
