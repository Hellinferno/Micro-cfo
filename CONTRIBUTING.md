# Contributing to MicroCFO

Thank you for your interest in contributing to MicroCFO! This document provides guidelines for contributions.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:

- Be respectful and considerate in all interactions
- Welcome newcomers and help them contribute
- Focus on constructive criticism
- Accept responsibility for mistakes

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Git
- PostgreSQL (optional, SQLite for development)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Micro-cfo.git
   cd Micro-cfo
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/Hellinferno/Micro-cfo.git
   ```

## Development Setup

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Copy environment configuration
cp config/.env.example .env
# Edit .env with your API keys

# Run development server
python src/integration_server.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_visual_auditor.py
```

## Making Contributions

### Types of Contributions

We welcome:
- 🐛 **Bug fixes**: Found a bug? Please report or fix it!
- ✨ **Features**: New features that align with our roadmap
- 📖 **Documentation**: Improvements to docs, comments, or examples
- 🧪 **Tests**: Additional test coverage
- 🎨 **UI/UX**: Frontend improvements

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### Commit Messages

Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(visual-auditor): add PDF batch processing
fix(gst-reconciler): handle missing GSTIN gracefully
docs(readme): update installation instructions
```

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes** and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Keep updated** with upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push** your branch:
   ```bash
   git push origin feature/your-feature
   ```

5. **Open PR** on GitHub:
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

### PR Requirements

- [ ] Tests pass (`pytest`)
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] No hardcoded API keys or secrets
- [ ] Commit messages follow conventions

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for all public functions

```python
def process_invoice(
    invoice_data: dict,
    validate: bool = True
) -> InvoiceResult:
    """
    Process an invoice and extract relevant data.
    
    Args:
        invoice_data: Raw invoice data dictionary
        validate: Whether to validate the extracted data
        
    Returns:
        InvoiceResult with extracted and validated data
        
    Raises:
        ValidationError: If validation fails and validate=True
    """
    ...
```

### TypeScript/React Style

- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks
- Prefer named exports

```typescript
interface InvoiceProps {
  data: Invoice;
  onValidate: (id: string) => void;
}

export function InvoiceCard({ data, onValidate }: InvoiceProps) {
  // Component implementation
}
```

### Testing Standards

- Aim for 80%+ code coverage
- Write unit tests for all new functions
- Use fixtures for test data
- Mock external API calls

## Security

- **Never commit API keys or secrets**
- Use environment variables for configuration
- Report security vulnerabilities privately to security@microcfo.com

## Questions?

- Open a GitHub Discussion for questions
- Join our community chat (if available)
- Email: dev@microcfo.com

---

Thank you for contributing to MicroCFO! 🎉
