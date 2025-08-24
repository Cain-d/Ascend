# Ascend - Fitness & Nutrition Tracker

A comprehensive full-stack application for tracking meals, bodyweight, and training performance with advanced analytics capabilities.

## 🚀 Tech Stack

**Backend:**
- FastAPI with Pydantic for data validation
- JWT authentication (python-jose + bcrypt)
- SQLite database with migration system
- Advanced analytics and prediction engine
- Comprehensive test suite with pytest

**Frontend:**
- React 19 with Vite for fast development
- Tailwind CSS for responsive design
- Axios for API communication
- Modern component architecture

**Infrastructure:**
- Production-ready with Docker support
- Easy migration to PostgreSQL/MySQL
- Scalable architecture for cloud deployment

## ✨ Features

### Core Functionality
- **User Authentication**: Secure JWT-based registration and login
- **Nutrition Tracking**: Log meals with detailed macro breakdowns
- **Weight Management**: Track bodyweight changes over time
- **Workout Logging**: Record exercises, sets, reps, and weights
- **Daily Summaries**: View comprehensive daily nutrition and activity data

### Advanced Analytics
- **Trend Analysis**: Identify patterns in weight and nutrition data
- **Performance Predictions**: AI-powered workout performance forecasting
- **Personalized Recommendations**: Custom macro targets based on goals
- **Correlation Insights**: Understand relationships between nutrition and performance
- **Background Processing**: Efficient handling of complex analytics computations

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd Ascend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (especially SECRET_KEY for production)
   ```

5. **Initialize database:**
   ```bash
   python run_migrations.py
   ```

6. **Start the API server:**
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at: http://127.0.0.1:8000
   
   Interactive API docs: http://127.0.0.1:8000/docs

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd ascend-frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://127.0.0.1:5173

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Backend tests
pytest tests/ -v

# Frontend tests (if configured)
cd ascend-frontend
npm test
```

## 📊 API Endpoints

### Authentication
- `POST /create_user` - Register new user
- `POST /login` - User authentication

### Core Features
- `GET/POST/DELETE /foods` - Nutrition tracking
- `GET/POST /weights` - Weight management
- `GET/POST /workouts` - Exercise logging
- `GET /daily_macros` - Daily nutrition summary

### Analytics
- `GET /analytics/trends` - Weight and nutrition trends
- `GET /analytics/predictions` - Performance forecasting
- `GET /analytics/recommendations` - Personalized suggestions
- `GET /analytics/insights` - Comprehensive dashboard data

## 🔒 Security

- JWT tokens for stateless authentication
- Password hashing with bcrypt
- Environment-based configuration
- CORS protection
- Input validation with Pydantic

## 🚀 Deployment

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here
DATABASE_PATH=data/ascend.db
CORS_ORIGINS=https://yourdomain.com
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Production Considerations
- Use a strong SECRET_KEY
- Configure appropriate CORS origins
- Consider PostgreSQL for production database
- Set up proper logging and monitoring
- Use HTTPS in production

## 📁 Project Structure

```
Ascend/
├── app/                    # Backend application
│   ├── main.py            # FastAPI application
│   ├── models.py          # Pydantic models
│   ├── auth.py            # Authentication logic
│   ├── queries.py         # Database operations
│   ├── analytics.py       # Analytics engine
│   └── predictions.py     # ML predictions
├── ascend-frontend/       # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── api.js         # API client
│   │   └── App.jsx        # Main application
├── tests/                 # Test suite
├── migrations/            # Database migrations
├── data/                  # SQLite database
└── docs/                  # Documentation and screenshots
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.





