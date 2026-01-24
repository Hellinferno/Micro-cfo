# Contributing to MicroCFO

Thank you for your interest in contributing to MicroCFO! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Hellinferno/Micro-cfo/issues)
2. If not, create a new issue using the bug report template
3. Provide detailed information including:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Relevant logs or screenshots

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue using the feature request template
3. Clearly describe the feature and its benefits
4. Discuss implementation approaches if applicable

### Pull Requests

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest tests/ -v
   
   # Run linting
   flake8 .
   
   # Test Docker build
   docker-compose build
   ```

4. **Commit your changes**
   - Use clear, descriptive commit messages
   - Follow conventional commits format:
     ```
     feat: add new feature
     fix: resolve bug in component
     docs: update documentation
     test: add test coverage
     refactor: improve code structure
     ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference related issues
   - Ensure all CI checks pass

## Development Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Node.js 20+ (for frontend)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Hellinferno/Micro-cfo.git
   cd Micro-cfo
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Initialize databases**
   ```bash
   python scripts/setup_legal_db.py
   python scripts/setup_scheme_db.py
   ```

5. **Run tests**
   ```bash
   pytest tests/ -v
   ```

### Docker Development

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests in container
docker-compose exec backend pytest -v

# Stop services
docker-compose down
```

## Code Style

### Python
- Follow PEP 8 guidelines
- Use type hints where applicable
- Maximum line length: 127 characters
- Use meaningful variable and function names

### JavaScript/React
- Follow ESLint configuration
- Use functional components with hooks
- Maintain consistent formatting with Prettier

## Testing

### Writing Tests
- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names
- Aim for high code coverage

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_integration_server.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update API documentation for endpoint changes
- Include examples for new features

## Project Structure

```
MicroCFO/
├── server.py              # Main MCP server
├── integration_server.py  # FastAPI integration
├── models.py              # Database models
├── routers/               # API endpoints
├── middleware/            # Middleware components
├── tasks/                 # Celery tasks
├── tests/                 # Test suite
├── frontend/              # React frontend
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## Commit Message Guidelines

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or auxiliary tool changes

Example:
```
feat: add subsidy calculation for textile sector

- Implement benefit calculation logic
- Add tests for edge cases
- Update documentation
```

## Review Process

1. All PRs require at least one approval
2. CI checks must pass
3. Code coverage should not decrease
4. Documentation must be updated
5. Breaking changes require discussion

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar questions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to MicroCFO! 🚀
