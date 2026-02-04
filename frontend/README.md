# StoryGraph Frontend

A React + TypeScript frontend for the StoryGraph manuscript editor and knowledge graph system.

## Features

- **Real-time Manuscript Editing** - WebSocket-based text editor
- **Entity Extraction Display** - View extracted characters, locations, objects, and events
- **Auto-processing** - Automatically processes paragraphs after user stops typing
- **Connection Status** - Visual indicator for WebSocket connection status
- **Responsive UI** - Built with Tailwind CSS

## Setup

### Prerequisites

- Node.js 16+
- The StoryGraph backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## Project Structure

```
src/
├── components/        # React components
│   ├── ManuscriptEditor.tsx
│   └── EntitySidebar.tsx
├── hooks/            # Custom React hooks
│   └── useWebSocket.ts
├── store.ts          # Zustand state management
├── App.tsx           # Main app component
├── main.tsx          # Entry point
└── index.css         # Global styles
```

## WebSocket Connection

The frontend connects to the backend WebSocket at:

```
ws://localhost:8000/ws/manuscript/{manuscriptId}
```

It sends paragraph data and receives extracted entities in real-time.

## Components

### ManuscriptEditor

Main text editor component with:

- Auto-save on pause
- Chapter/paragraph tracking
- Processing status indicator

### EntitySidebar

Displays extracted entities grouped by type:

- Characters (blue)
- Locations (green)
- Objects (orange)
- Events (purple)

## Environment Variables

Create a `.env` file:

```
VITE_BACKEND_URL=ws://localhost:8000
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript type checking
