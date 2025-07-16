# Vietnamese Menu Analyzer

A high-standard web application for analyzing Vietnamese menu images using AI. Built with FastAPI, modern JavaScript, and integrated with Vietnamese AI models.

## Features

- **AI-Powered Menu Extraction**: Uses Vintern-1B (Vietnamese AI model) to extract dish names and prices from menu images
- **Recipe Generation**: Automatically generates authentic Vietnamese recipes for each dish
- **Image Search**: Integrates with Google Images to provide visual references for each dish
- **Modern UI**: Clean, responsive interface with split-screen layout
- **Real-time Processing**: Background tasks for recipe generation
- **Caching**: Redis-based caching for improved performance
- **Vietnamese Localization**: Fully localized for Vietnamese users

## Architecture

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   └── logging.py       # Logging setup
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── services/
│       ├── ocr_service.py   # AI menu extraction
│       ├── image_service.py # Google Images integration
│       ├── recipe_service.py # Recipe generation
│       └── cache_service.py # Redis caching
├── static/
│   ├── css/
│   │   └── styles.css       # Modern responsive CSS
│   ├── js/
│   │   ├── api.js          # API client
│   │   └── app.js          # Frontend logic
│   └── index.html          # Main HTML interface
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── docker-compose.yml     # Docker Compose setup
```

## Quick Start

### Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd vietnamese-menu-analyzer
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Start Redis** (optional):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or local Redis
redis-server
```

5. **Run the application**:
```bash
python -m app.main
```

6. **Access the app**:
- Web interface: http://localhost:8000
- API docs: http://localhost:8000/docs

### Docker Deployment

1. **Build and run**:
```bash
docker-compose up --build
```

2. **Access the app**:
- Web interface: http://localhost:8000

## API Endpoints

### Menu Analysis
- `POST /api/v1/analyze-menu` - Analyze menu image
- `GET /api/v1/analysis/{request_id}` - Get analysis results
- `GET /api/v1/recipes/{request_id}/{dish_name}` - Get recipe for specific dish

### Health Check
- `GET /health` - Application health status

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `HF_API_TOKEN` | Hugging Face API token for Vintern-1B | `hf_xxx...` |
| `GOOGLE_API_KEY` | Google Custom Search API key | `AIza...` |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID | `xxx:yyy...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |

### Optional Configuration

- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `MAX_FILE_SIZE`: Maximum upload file size in bytes (default: 5MB)

## Usage

1. **Upload Menu Image**: Drag and drop or select a Vietnamese menu image
2. **AI Analysis**: The app extracts dish names and prices using Vintern-1B
3. **View Results**: See dishes with images and prices in the left panel
4. **Get Recipes**: Click on any dish to view detailed Vietnamese recipe
5. **Save Favorites**: Recipes are cached for quick access

## Technology Stack

### Backend
- **FastAPI**: Modern, fast Python web framework
- **Pydantic**: Data validation using Python type annotations
- **httpx**: Async HTTP client for API calls
- **Redis**: Caching and session management
- **Python 3.8+**: Modern Python features

### Frontend
- **Vanilla JavaScript**: ES6+ modules for modern browsers
- **CSS Grid/Flexbox**: Responsive layout
- **Fetch API**: Modern HTTP client
- **Drag & Drop**: Native file upload

### AI Integration
- **Vintern-1B**: Vietnamese language AI model for text extraction
- **Google Images**: Visual dish references
- **Background Tasks**: Async recipe generation

## Development

### Project Structure

```
vietnamese-menu-analyzer/
├── app/
│   ├── api/           # REST API endpoints
│   ├── core/          # Core utilities and config
│   ├── models/        # Data models
│   └── services/      # Business logic services
├── static/            # Frontend assets
├── tests/             # Test files
└── docs/              # Documentation
```

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
flake8 app/
```

## Deployment

### Production Environment

1. **Environment variables**:
```bash
export DEBUG=false
export HF_API_TOKEN=your_token
export GOOGLE_API_KEY=your_key
export REDIS_URL=redis://your-redis-server:6379
```

2. **Docker deployment**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Systemd service**:
```bash
# Copy service file
sudo cp deploy/menu-analyzer.service /etc/systemd/system/
sudo systemctl enable menu-analyzer
sudo systemctl start menu-analyzer
```

### Cloud Deployment

**Heroku**:
```bash
# Deploy to Heroku
heroku create vietnamese-menu-analyzer
git push heroku main
```

**AWS ECS**:
```bash
# Deploy to AWS
aws ecs register-task-definition --cli-input-json file://deploy/task-definition.json
aws ecs update-service --cluster menu-cluster --service menu-service
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the docs/ directory for detailed guides

## Roadmap

- [ ] Multi-language support (English, Vietnamese)
- [ ] Recipe ratings and reviews
- [ ] User accounts and favorites
- [ ] Restaurant database integration
- [ ] Mobile app (React Native)
- [ ] Offline mode with service workers
- [ ] Advanced image processing (multiple dishes)
- [ ] Nutrition calculation
- [ ] Video recipe generation
- [ ] Social sharing features