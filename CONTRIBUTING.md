# 🤝 Contributing to Traqify

Thank you for your interest in contributing to Traqify! This document provides guidelines and information for contributors.

## 🌟 How to Contribute

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs

### 💡 Suggesting Features

Feature requests are welcome! Please provide:

- **Clear description** of the feature
- **Use case** and motivation
- **Possible implementation** ideas (if any)
- **Examples** from other applications (if relevant)

### 🔧 Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
6. **Push to your branch**
7. **Create a Pull Request**

## 📋 Development Guidelines

### 🐍 Python Code Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for all classes and methods
- Keep functions focused and small
- Use meaningful variable and function names

### 🏗️ Code Structure

```
src/
├── core/           # Core functionality
├── modules/        # Feature modules
├── ui/            # User interface components
└── utils/         # Utility functions
```

### 📝 Documentation

- Update documentation for new features
- Include docstrings for all public methods
- Add comments for complex logic
- Update README.md if needed

### 🧪 Testing

- Write tests for new features
- Ensure all existing tests pass
- Test on multiple platforms if possible
- Include edge cases in tests

## 🚀 Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Setup Steps

1. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/traqify.git
   cd traqify
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If exists
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 🔍 Code Review Process

### Pull Request Guidelines

- **Clear title** and description
- **Reference related issues** (e.g., "Fixes #123")
- **Small, focused changes** (easier to review)
- **Updated tests** and documentation
- **No merge conflicts**

### Review Criteria

- Code follows style guidelines
- Functionality works as expected
- Tests pass and cover new code
- Documentation is updated
- No breaking changes (unless discussed)

## 🏷️ Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): brief description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(expense): add category filtering
fix(auth): resolve login timeout issue
docs(setup): update installation instructions
```

## 🎯 Areas for Contribution

### 🔥 High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Security enhancements
- Documentation improvements

### 💡 Feature Ideas
- Mobile app development
- Additional data export formats
- Advanced analytics and reporting
- Integration with more financial services
- Improved data visualization
- Multi-language support

### 🛠️ Technical Improvements
- Code refactoring and optimization
- Test coverage improvements
- CI/CD pipeline enhancements
- Database migration tools
- API development

## 📞 Getting Help

### 💬 Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: [your.email@example.com](mailto:your.email@example.com)

### 📚 Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Git Best Practices](https://git-scm.com/book)

## 🏆 Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Given credit in documentation and README

## 📄 License

By contributing to Traqify, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Every contribution, no matter how small, is valuable and appreciated. Thank you for helping make Traqify better for everyone!

---

**Questions?** Feel free to reach out via [GitHub Issues](https://github.com/yourusername/traqify/issues) or email [your.email@example.com](mailto:your.email@example.com).
