# 🚀 Serverless Python Backend Tutorial

> **Build production-ready serverless APIs using Domain Driven Design, CLEAN Architecture, and AWS CDK**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-2.0+-orange.svg)](https://aws.amazon.com/cdk/)

## 📖 Overview

This repository contains a **comprehensive, step-by-step tutorial** for building a production-ready **Task Management API** using modern serverless architecture on AWS. Learn industry best practices through hands-on implementation of Domain Driven Design, CLEAN Architecture, and Infrastructure as Code.

### 🎯 What You'll Learn

- **Domain Driven Design (DDD)** - Structure business logic with clear boundaries
- **CLEAN Architecture** - Build maintainable and testable applications  
- **Event-Driven Architecture** - Implement asynchronous processing with SNS/SQS
- **Infrastructure as Code** - Deploy production infrastructure with AWS CDK
- **Testing Strategy** - Unit, integration, and end-to-end testing
- **Production Practices** - Monitoring, observability, and error handling

### 🏗️ What You'll Build

A complete **Task Management REST API** with:

- ✅ **CRUD Operations** - Create, read, update, and complete tasks
- ✅ **Event-Driven Processing** - Asynchronous notifications and workflows
- ✅ **Production Infrastructure** - Auto-scaling, monitoring, and logging
- ✅ **Comprehensive Testing** - Full test coverage across all layers
- ✅ **API Documentation** - Interactive Swagger/OpenAPI specification
- ✅ **Single-Table DynamoDB** - Optimized data modeling and access patterns

## 🏛️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │     Lambda      │    │    DynamoDB     │
│                 │───>│   Functions     │───>│   Single Table  │
│   + Swagger     │    │   (Python 3.12) │    │   Design        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   SNS Topic     │───>│   SQS Queue     │
                       │  (Domain Events)│    │  + Processing   │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+** - [Download here](https://www.python.org/downloads/)
- **Poetry** - [Install guide](https://python-poetry.org/docs/#installation)
- **Node.js 18+** - [Download here](https://nodejs.org/) (for AWS CDK)
- **AWS CLI** - [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **AWS Account** with appropriate permissions

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/ettoreaquino/scafolddd.git
cd scafolddd

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Verify setup
python --version && poetry --version
```

## 📋 Two Ways to Follow This Tutorial

### 🎯 Option 1: GitHub Issues (Recommended)

Work through **[9 structured GitHub Issues](https://github.com/ettoreaquino/scafolddd/issues)** that break down the tutorial into manageable tasks:

1. **[Part 1: Project Setup](https://github.com/ettoreaquino/scafolddd/issues/1)** - Initialize development environment
2. **[Part 2: Domain Layer](https://github.com/ettoreaquino/scafolddd/issues/2)** - Implement core business logic
3. **[Part 3: Application Layer](https://github.com/ettoreaquino/scafolddd/issues/3)** - Build services and orchestration
4. **[Part 4: Infrastructure Layer](https://github.com/ettoreaquino/scafolddd/issues/4)** - Connect to external services
5. **[Part 5: API Adapter Layer](https://github.com/ettoreaquino/scafolddd/issues/5)** - Expose REST endpoints
6. **[Part 6: CDK Infrastructure](https://github.com/ettoreaquino/scafolddd/issues/6)** - Deploy to AWS
7. **[Part 7: Testing Implementation](https://github.com/ettoreaquino/scafolddd/issues/7)** - Comprehensive test coverage
8. **[Part 8: Deployment and Testing](https://github.com/ettoreaquino/scafolddd/issues/8)** - End-to-end verification
9. **[Part 9: Production Readiness](https://github.com/ettoreaquino/scafolddd/issues/9)** - Monitoring and security

Each issue includes:
- ✅ **Detailed task lists** with checkboxes to track progress
- 🎯 **Clear acceptance criteria** for completion
- 🧪 **Verification scripts** to validate each step
- 📝 **Code examples** and implementation guidance

### 📚 Option 2: Comprehensive Tutorial

Follow the detailed written tutorial in **[`docs/TUTORIAL.md`](docs/TUTORIAL.md)** for in-depth explanations, architectural decisions, and complete code walkthroughs.

## 🗂️ Project Structure

Following **CLEAN Architecture** principles:

```
src/
├── domain/                    # 🏛️ Pure business logic
│   ├── entities/              # Business entities
│   ├── value_objects/         # Immutable domain objects  
│   ├── repositories/          # Abstract interfaces
│   └── events/                # Domain events
├── application/               # 🎯 Service orchestration
│   └── services/              # Business services
├── infrastructure/            # 🔧 External dependencies
│   ├── repositories/          # DynamoDB implementations
│   └── messaging/             # SNS/SQS adapters
├── adapters/                  # 🔌 Entry points
│   ├── api/                   # Lambda handlers
│   └── events/                # Event processors
└── commons/                   # 🛠️ Common utilities
```

## 🧪 Verification

Each tutorial part includes verification scripts to ensure everything works correctly:

```bash
# Example: Verify domain layer implementation
poetry run python test_domain_verification.py

# Expected output:
# 🧪 Testing Domain Layer Setup...
# ✅ TaskId generated: task-123e4567...
# ✅ Task entity working correctly
# 🎉 Domain layer working correctly!
```

## 🚀 Deployment

Deploy your completed application to AWS:

```bash
# Deploy infrastructure with CDK
cd infrastructure/cdk
cdk deploy BackendTutorialStagingStack

# Verify deployment
poetry run python scripts/test_deployed_api.py <API_URL>
```

## 🎓 Learning Path

- **Beginners**: Start with GitHub Issues #1-3, focus on understanding the concepts
- **Intermediate**: Complete all issues, experiment with custom extensions  
- **Advanced**: Study the detailed tutorial, optimize for production use cases

## 🤝 Contributing

Found an issue or want to improve the tutorial? 

- **Report bugs**: Open a GitHub issue
- **Suggest improvements**: Submit a pull request
- **Ask questions**: Start a GitHub discussion

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to start?** 🎉 

👉 **Begin with [GitHub Issue #1](https://github.com/ettoreaquino/scafolddd/issues/1)** or explore **[`docs/TUTORIAL.md`](docs/TUTORIAL.md)** for the complete guide.
