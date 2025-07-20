# 🚀 Serverless Python Backend Tutorial

> **Build production-ready serverless APIs using Domain Driven Design, CLEAN Architecture, and AWS CDK**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-2.0+-orange.svg)](https://aws.amazon.com/cdk/)

## 📖 Overview

This repository contains a comprehensive tutorial for building a **Task Management API** using modern serverless architecture on AWS. The tutorial demonstrates industry best practices and clean code principles that you can apply to real-world projects.

### 🎯 What You'll Learn

- **Domain Driven Design (DDD)** - Structure business logic with clear boundaries
- **CLEAN Architecture** - Build maintainable and testable applications
- **SOLID Principles** - Write flexible and extensible code
- **Event-Driven Architecture** - Implement asynchronous processing
- **Infrastructure as Code** - Deploy with AWS CDK
- **Production Practices** - Monitoring, logging, and error handling

### 🏗️ What You'll Build

A complete **Task Management REST API** featuring:

- ✅ **CRUD Operations** - Create, read, update, and complete tasks
- ✅ **Event-Driven Notifications** - Asynchronous processing with SNS/SQS
- ✅ **Production-Ready Infrastructure** - Auto-scaling, monitoring, and logging
- ✅ **Comprehensive Testing** - Unit, integration, and end-to-end tests
- ✅ **API Documentation** - Swagger/OpenAPI specification
- ✅ **Single-Table DynamoDB Design** - Optimized for performance and cost

## 🏛️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │     Lambda      │    │    DynamoDB     │
│                 │───▶│   Functions     │───▶│   Single Table  │
│   + Swagger     │    │   (Python 3.12)│    │   Design        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SNS Topic     │───▶│   SQS Queue     │
                       │  (Domain Events)│    │  + Processing   │
                       └─────────────────┘    └─────────────────┘
```

### 🗂️ Project Structure

The tutorial follows **CLEAN Architecture** principles with clear separation of concerns:

```
backend-tutorial/
├── src/
│   ├── domain/                    # 🏛️ Pure business logic
│   │   ├── entities/              # Business entities (Task)
│   │   ├── value_objects/         # Immutable domain objects
│   │   ├── services/              # Domain services
│   │   ├── repositories/          # Abstract interfaces
│   │   ├── events/                # Domain events
│   │   └── exceptions/            # Domain-specific errors
│   ├── application/               # 🎯 Use case orchestration
│   │   ├── use_cases/             # Business use cases
│   │   ├── commands/              # CQRS commands
│   │   ├── queries/               # CQRS queries
│   │   └── handlers/              # Command/query handlers
│   ├── infrastructure/            # 🔧 External dependencies
│   │   ├── repositories/          # DynamoDB implementations
│   │   ├── messaging/             # SNS/SQS adapters
│   │   └── email/                 # SES adapters
│   ├── adapters/                  # 🔌 Entry points
│   │   ├── api/                   # Lambda handlers
│   │   └── events/                # Event processors
│   └── shared/                    # 🛠️ Shared utilities
├── tests/                         # 🧪 Comprehensive test suite
├── infrastructure/cdk/            # ☁️ AWS CDK infrastructure
├── docs/                          # 📚 Documentation
└── scripts/                       # 🚀 Deployment scripts
```

## 🔧 Prerequisites

Before starting the tutorial, ensure you have:

### Required Software

- **Python 3.12+** - [Download here](https://www.python.org/downloads/)
- **Poetry** - [Install guide](https://python-poetry.org/docs/#installation)
- **Node.js 18+** - [Download here](https://nodejs.org/) (for AWS CDK)
- **AWS CLI** - [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### AWS Setup

- **AWS Account** with appropriate permissions
- **AWS CLI configured** with credentials
- **AWS CDK CLI** installed: `npm install -g aws-cdk`

### Quick Verification

Run these commands to verify your setup:

```bash
python3.12 --version    # Should show 3.12.x
poetry --version        # Should show 1.0+
node --version          # Should show 18.x+
aws --version           # Should show aws-cli/2.x+
cdk --version           # Should show 2.x+
```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/backend-tutorial.git
cd backend-tutorial
```

### 2. Set Up Dependencies

```bash
# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell

# Install CDK dependencies (if following infrastructure sections)
cd infrastructure/cdk
npm install
cd ../..
```

### 3. Follow the Tutorial

The complete tutorial is available in [`docs/TUTORIAL.md`](docs/TUTORIAL.md). It's structured in progressive steps:

1. **Project Setup** - Initialize the development environment
2. **Domain Layer** - Implement core business logic
3. **Application Layer** - Build use cases and orchestration
4. **Infrastructure Layer** - Connect to external services
5. **API Layer** - Expose REST endpoints
6. **CDK Infrastructure** - Deploy to AWS
7. **Testing Strategy** - Comprehensive test coverage
8. **Production Deployment** - Go live with monitoring

### 4. Verify Your Progress

Each major section includes verification steps. For example, after completing the Domain Layer:

```bash
poetry run python test_domain_verification.py
```

Expected output:
```
🧪 Testing Domain Layer Setup...
✅ TaskId generated: task-123e4567-e89b-12d3-a456-426614174000
✅ UserId created: user-123
✅ TaskStatus: pending
✅ Created task: Learn Domain Design
✅ Generated 3 events
🎉 Domain layer working correctly!
```

## 🧠 Key Concepts Explained

### Domain Driven Design (DDD)

- **Entities** - Objects with identity and lifecycle (e.g., Task)
- **Value Objects** - Immutable objects representing concepts (e.g., TaskId, UserId)
- **Domain Events** - Important business occurrences (e.g., TaskCompleted)
- **Repositories** - Abstract data access without implementation details
- **Domain Services** - Business logic that doesn't fit in entities

### CLEAN Architecture

- **Independence** - Business logic doesn't depend on frameworks
- **Testability** - Easy to test without external dependencies
- **Flexibility** - Swap implementations without changing business logic
- **Maintainability** - Clear boundaries and responsibilities

### Event-Driven Architecture

- **Loose Coupling** - Services communicate through events
- **Scalability** - Async processing handles load spikes
- **Reliability** - Events can be replayed and processed reliably
- **Auditability** - Complete trace of business events

### Serverless Benefits

- **Cost Efficiency** - Pay only for what you use
- **Auto Scaling** - Handles traffic spikes automatically
- **Reduced Ops** - No server management required
- **High Availability** - Built-in redundancy and failover

## 🧪 Testing Strategy

The tutorial covers multiple testing levels:

### Unit Tests
```bash
poetry run pytest tests/unit/ -v
```

### Integration Tests
```bash
poetry run pytest tests/integration/ -v
```

### End-to-End Tests
```bash
poetry run pytest tests/e2e/ -v
```

## 🚀 Deployment

### Local Development
```bash
# Run individual functions locally
poetry run python -m src.adapters.api.create_task

# Test domain layer
poetry run python test_domain_verification.py
```

### AWS Deployment
```bash
# Deploy infrastructure
cd infrastructure/cdk
cdk deploy

# Run deployment tests
cd ../..
poetry run python scripts/test_deployed_api.py <API_URL>
```

## 📚 Learning Path

### Beginner (New to DDD/CLEAN Architecture)
1. Start with **Domain Layer** concepts
2. Focus on understanding **Entities** and **Value Objects**
3. Complete the verification scripts at each step
4. Skip CDK deployment initially, focus on code structure

### Intermediate (Familiar with Clean Code)
1. Study the **Architecture Decisions** in each layer
2. Implement **Custom Extensions** (additional use cases)
3. Focus on **Testing Strategies**
4. Deploy to AWS and monitor performance

### Advanced (Ready for Production)
1. Customize **Infrastructure** for your use case
2. Implement **Advanced Patterns** (CQRS, Event Sourcing)
3. Add **Security** and **Compliance** features
4. Optimize for **Performance** and **Cost**

## 🛠️ Common Issues & Solutions

### Import Errors
```bash
# Ensure you're in the poetry environment
poetry shell

# Verify Python path
poetry run python -c "import sys; print(sys.path)"
```

### DateTime Issues
- The tutorial uses `datetime.now(timezone.utc)` for Python 3.12+ compatibility
- Older Python versions may need `datetime.utcnow()` (deprecated)

### AWS Permissions
- Ensure your AWS credentials have DynamoDB, Lambda, API Gateway, SNS, and SQS permissions
- Consider using AWS CloudShell for consistent environment

## 🤝 Contributing

This tutorial is designed to be educational and accessible. If you find:

- **Errors or typos** - Please open an issue
- **Improvements** - Submit a pull request
- **Questions** - Start a discussion

### Development Setup
```bash
# Install development dependencies
poetry install --with dev

# Run linting
poetry run black src/ tests/
poetry run isort src/ tests/

# Run type checking
poetry run mypy src/
```

## 📜 License

This tutorial is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This tutorial draws inspiration from:

- **Clean Architecture** by Robert C. Martin
- **Domain-Driven Design** by Eric Evans
- **AWS Well-Architected Framework**
- **Python community best practices**

## 📞 Support

- 📖 **Documentation**: [`docs/TUTORIAL.md`](docs/TUTORIAL.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/backend-tutorial/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/backend-tutorial/discussions)
- 📧 **Contact**: [your.email@example.com](mailto:your.email@example.com)

---

**Happy coding!** 🎉 Start your journey with [`docs/TUTORIAL.md`](docs/TUTORIAL.md)
