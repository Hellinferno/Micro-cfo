# Contributing to MicroCFO

Thank you for your interest in contributing to MicroCFO! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ (for local development)
- Node.js 18+ (for frontend development)

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/microcfo.git
cd microcfo
```

2. Set up Python environment:
```bash
python setup.py
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize databases:
```bash
python setup_legal_db.py
python setup_scheme_db.py
```

5. Run tests:
```bash
pytest test_*.py -v
```

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and test:
```bash
pytest test_*.py -v
```

3. Run linting:
```bash
flake8 . --max-line-length=127
```

4. Commit with descriptive messages:
```bash
git commit -m "feat: add new feature description"
```

5. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Maximum line length: 127 characters
- Use type hints where appropriate
- Document functions with docstrings

### Testing Requirements
- Write unit tests for new features
- Maintain test coverage above 80%
- Include integration tests for API endpoints
- Use property-based testing for complex logic

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

## Testing

### Running Tests
```bash
# All tests
pytest test_*.py -v

# Specific test file
pytest test_visual_auditor.py -v

# With coverage
pytest test_*.py --cov=. --cov-report=html

# Property-based tests
pytest test_*_properties.py -v
```

### Docker Testing
```bash
# Build and test with Docker
docker-compose -f docker-compose.dev.yml up --build

# Run tests in container
docker-compose exec backend pytest -v
```

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Include parameter types and return types
- Provide usage examples for complex functions

### Project Documentation
- Update README.md for user-facing changes
- Update technical docs in `.kiro/steering/` for architecture changes
- Add deployment notes to DEPLOYMENT_READY.md

## Pull Request Process

1. Update documentation for your changes
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md if applicable
5. Request review from maintainers
6. Address review feedback
7. Squash commits if requested

## Code Review Guidelines

### For Authors
- Keep PRs focused and reasonably sized
- Provide context in PR description
- Respond to feedback promptly
- Test thoroughly before requesting review

### For Reviewers
- Be constructive and respectful
- Focus on code quality and maintainability
- Check for security issues
- Verify test coverage

## Security

### Reporting Vulnerabilities
- Do NOT open public issues for security vulnerabilities
- Email security concerns to: [security contact]
- Include detailed reproduction steps
- Allow time for fixes before disclosure

### Security Best Practices
- Never commit API keys or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP guidelines

## Getting Help

- Check existing issues and documentation
- Join our community discussions
- Ask questions in pull requests
- Contact maintainers for guidance

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
