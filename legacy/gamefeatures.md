# Game Features & Functionality

## ✅ Implemented Features

### Core Gameplay
*   **Riddle Generation**: Dynamic riddle generation using AI.
*   **Difficulty Levels**: 
    *   Easy, Medium, Hard, Extreme, Custom.
    *   Dynamic difficulty scaling using different prompts.
*   **Daily Challenges**: Personalized daily riddles that reset every 24 hours.
*   **Scoring System**: Points awarded based on difficulty and attempts.

### User System
*   **Authentication**: Secure Register and Login.
*   **Multi-User Support**: Isolated game states, settings, and histories for different users.
*   **Persistent Sessions**: Users can leave and return to resume their current riddles.

### Social & Competitive
*   **Leaderboards**:
    *   Global Leaderboard (Top players).
    *   Local/Personal ranking.

### Customization (Settings)
*   **Thematic System**: 
    *   Support for visual themes (Cyberpunk, Fantasy, Horror).
    *   Themes influence UI styling and AI System Prompts (e.g., "Write a riddle in the style of a wizard").
*   **UI Customization**:
    *   User-defined primary/accent colors.
    *   Custom background images.
*   **AI Model Selection**:
    *   Option to switch between Ollama variants or Online Providers (OpenAI, Anthropic).
    *   Storage for user API keys.

### Premium Features
*   **Subscription Simulation**: Ability to "upgrade" to Premium.
*   **Content Unlocking**: Premium status unlocks "Extreme" difficulties and special themes.

---

## 🛠 Technical Features
*   **Hybrid AI Engine**: 
    *   **Ollama**: Local, private, free (Neural-Chat 7B).
    *   **Fallback Safety**: Auto-switch to Local Transformers or Mock data if Ollama fails.
    *   **Online APIs**: Framework for connecting to GPT-4/Claude.
*   **Robust Architecture**:
    *   **Backend**: FastAPI with async support.
    *   **Database**: MongoDB for flexible JSON document storage (Users, Riddles, Settings).
    *   **Frontend**: React.js with responsive design.
    *   **Containerization**: Docker Compose for Database and AI services.

---

## 📝 Recent Todo Items (Completed)
*Verified from Todo list*

- [x] **User Settings UI**: Interface for color/background customization.
- [x] **Thematic System**: Backend prompt injection based on selected theme.
- [x] **Difficulty Unlocks**: Fixed bugs preventing access to high-tier levels.
- [x] **Model Management**: Decoupled ModelManager service.
- [x] **Online Mode**: Foundation for external API integrations.
- [x] **Leaderboard Pages**: dedicated routing and display tables.
