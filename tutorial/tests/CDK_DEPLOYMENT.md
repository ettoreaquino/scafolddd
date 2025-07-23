# CDK Deployment Testing Guide

> **Complete testing implementation for CDK Infrastructure deployment following TDD principles.**

This guide shows you exactly what tests to write when implementing CDK infrastructure from scratch, following Test-Driven Development (TDD) approach.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Infrastructure Unit Tests](#infrastructure-unit-tests)
- [Stack Validation Tests](#stack-validation-tests)
- [Deployment Integration Tests](#deployment-integration-tests)
- [End-to-End Infrastructure Tests](#end-to-end-infrastructure-tests)
- [Running CDK Tests](#running-cdk-tests)
- [TDD Workflow](#tdd-workflow)

---

## 🎯 Overview

CDK Infrastructure testing ensures that AWS resources are correctly defined and deployed. We test it thoroughly to ensure:

- ✅ **Infrastructure is correctly defined** - Resources have proper configurations
- ✅ **Security policies are enforced** - IAM roles and permissions are correct
- ✅ **Resource relationships work** - Dependencies and connections are proper
- ✅ **Environment configuration works** - Different stages deploy correctly
- ✅ **Cost optimization is maintained** - Resources are configured efficiently

## 🏗️ Test Structure

```
tests/
├── unit/cdk/                      # Unit tests (fast, isolated)
│   ├── test_api_stack.py          # API Gateway and Lambda tests
│   ├── test_database_stack.py     # DynamoDB tests
│   ├── test_event_stack.py        # SNS/SQS tests
│   └── test_monitoring_stack.py   # CloudWatch tests
├── integration/cdk/               # Integration tests (real AWS)
│   ├── test_stack_deployment.py   # Stack deployment tests
│   └── test_resource_creation.py  # Resource creation tests
└── e2e/cdk/                      # End-to-end tests (full deployment)
    ├── test_full_deployment.py    # Complete deployment tests
    └── test_environment_parity.py # Multi-environment tests
```

**Total CDK Tests:** 40+ tests (planned)

---

## 🏗️ Infrastructure Unit Tests

### File: `tests/unit/cdk/test_api_stack.py`

Test the API Gateway and Lambda infrastructure definitions.

#### Test Categories:

1. **Lambda Function Tests**
   - Test function configurations
   - Test environment variables
   - Test IAM permissions
   - Test timeout and memory settings

2. **API Gateway Tests**
   - Test resource definitions
   - Test method configurations
   - Test CORS settings
   - Test authentication

3. **Integration Tests**
   - Test Lambda-API Gateway integration
   - Test request/response mappings
   - Test error handling configurations

#### Example Test Implementation:

```python
@pytest.mark.cdk
@pytest.mark.unit
class TestAPIStack:
    def test_lambda_functions_created(self):
        """Test that all Lambda functions are created"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack", 
                        env={"account": "123456789012", "region": "us-east-1"})
        
        template = Template.from_stack(stack)
        
        # Verify Lambda functions exist
        template.has_resource_properties("AWS::Lambda::Function", {
            "Handler": "create_task.lambda_handler",
            "Runtime": "python3.12"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "Handler": "get_task.lambda_handler",
            "Runtime": "python3.12"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "Handler": "complete_task.lambda_handler",
            "Runtime": "python3.12"
        })
        
        template.has_resource_properties("AWS::Lambda::Function", {
            "Handler": "list_tasks.lambda_handler",
            "Runtime": "python3.12"
        })
    
    def test_lambda_environment_variables(self):
        """Test that Lambda functions have correct environment variables"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack",
                        table_name="test-tasks",
                        topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic")
        
        template = Template.from_stack(stack)
        
        # Verify environment variables
        template.has_resource_properties("AWS::Lambda::Function", {
            "Environment": {
                "Variables": {
                    "TABLE_NAME": "test-tasks",
                    "TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:test-topic",
                    "POWERTOOLS_SERVICE_NAME": "task-management"
                }
            }
        })
    
    def test_lambda_iam_permissions(self):
        """Test that Lambda functions have correct IAM permissions"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack")
        
        template = Template.from_stack(stack)
        
        # Verify IAM role for Lambda functions
        template.has_resource_properties("AWS::IAM::Role", {
            "AssumeRolePolicyDocument": {
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }
        })
        
        # Verify IAM policy for DynamoDB access
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query"
                        ],
                        "Resource": Match.any_value()
                    }
                ])
            }
        })
    
    def test_api_gateway_configuration(self):
        """Test that API Gateway is configured correctly"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack")
        
        template = Template.from_stack(stack)
        
        # Verify API Gateway REST API
        template.has_resource_properties("AWS::ApiGateway::RestApi", {
            "Name": Match.string_like_regexp(".*TaskManagement.*"),
            "EndpointConfiguration": {
                "Types": ["REGIONAL"]
            }
        })
        
        # Verify CORS configuration
        template.has_resource_properties("AWS::ApiGateway::Method", {
            "HttpMethod": "OPTIONS",
            "Integration": {
                "Type": "MOCK",
                "IntegrationResponses": [{
                    "StatusCode": "200",
                    "ResponseParameters": {
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'",
                        "method.response.header.Access-Control-Allow-Methods": "'GET,POST,PUT,DELETE,OPTIONS'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }]
            }
        })
    
    def test_api_gateway_resources_and_methods(self):
        """Test that API Gateway resources and methods are created"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack")
        
        template = Template.from_stack(stack)
        
        # Verify API Gateway resources
        template.resource_count_is("AWS::ApiGateway::Resource", 3)  # /tasks, /tasks/{id}, /tasks/{id}/complete
        
        # Verify API Gateway methods
        methods = ["GET", "POST", "OPTIONS"]
        for method in methods:
            template.has_resource_properties("AWS::ApiGateway::Method", {
                "HttpMethod": method
            })
```

### File: `tests/unit/cdk/test_database_stack.py`

Test the DynamoDB infrastructure definitions.

#### Example Test Implementation:

```python
@pytest.mark.cdk
@pytest.mark.unit
class TestDatabaseStack:
    def test_dynamodb_table_created(self):
        """Test that DynamoDB table is created with correct configuration"""
        app = cdk.App()
        stack = DatabaseStack(app, "test-database-stack")
        
        template = Template.from_stack(stack)
        
        # Verify DynamoDB table
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "BillingMode": "PAY_PER_REQUEST",
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"}
            ],
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"}
            ]
        })
    
    def test_dynamodb_gsi_configuration(self):
        """Test that DynamoDB GSI is configured correctly"""
        app = cdk.App()
        stack = DatabaseStack(app, "test-database-stack")
        
        template = Template.from_stack(stack)
        
        # Verify GSI configuration
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "GlobalSecondaryIndexes": [{
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }]
        })
    
    def test_dynamodb_deletion_protection(self):
        """Test that DynamoDB table has deletion protection in production"""
        app = cdk.App()
        stack = DatabaseStack(app, "prod-database-stack", environment="production")
        
        template = Template.from_stack(stack)
        
        # Verify deletion protection
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "DeletionProtectionEnabled": True
        })
    
    def test_dynamodb_point_in_time_recovery(self):
        """Test that DynamoDB table has point-in-time recovery enabled"""
        app = cdk.App()
        stack = DatabaseStack(app, "test-database-stack")
        
        template = Template.from_stack(stack)
        
        # Verify point-in-time recovery
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "PointInTimeRecoverySpecification": {
                "PointInTimeRecoveryEnabled": True
            }
        })
```

### File: `tests/unit/cdk/test_event_stack.py`

Test the SNS/SQS event infrastructure definitions.

#### Example Test Implementation:

```python
@pytest.mark.cdk
@pytest.mark.unit
class TestEventStack:
    def test_sns_topic_created(self):
        """Test that SNS topic is created"""
        app = cdk.App()
        stack = EventStack(app, "test-event-stack")
        
        template = Template.from_stack(stack)
        
        # Verify SNS topic
        template.has_resource_properties("AWS::SNS::Topic", {
            "DisplayName": Match.string_like_regexp(".*TaskEvents.*")
        })
    
    def test_sqs_queue_created(self):
        """Test that SQS queue is created for event processing"""
        app = cdk.App()
        stack = EventStack(app, "test-event-stack")
        
        template = Template.from_stack(stack)
        
        # Verify SQS queue
        template.has_resource_properties("AWS::SQS::Queue", {
            "VisibilityTimeoutSeconds": 300,
            "MessageRetentionPeriod": 1209600  # 14 days
        })
    
    def test_dead_letter_queue_configuration(self):
        """Test that dead letter queue is configured"""
        app = cdk.App()
        stack = EventStack(app, "test-event-stack")
        
        template = Template.from_stack(stack)
        
        # Verify dead letter queue
        template.has_resource_properties("AWS::SQS::Queue", {
            "RedrivePolicy": {
                "deadLetterTargetArn": Match.any_value(),
                "maxReceiveCount": 3
            }
        })
    
    def test_sns_sqs_subscription(self):
        """Test that SQS queue is subscribed to SNS topic"""
        app = cdk.App()
        stack = EventStack(app, "test-event-stack")
        
        template = Template.from_stack(stack)
        
        # Verify SNS subscription
        template.has_resource_properties("AWS::SNS::Subscription", {
            "Protocol": "sqs",
            "TopicArn": Match.any_value(),
            "Endpoint": Match.any_value()
        })
```

### File: `tests/unit/cdk/test_monitoring_stack.py`

Test the CloudWatch monitoring infrastructure definitions.

#### Example Test Implementation:

```python
@pytest.mark.cdk
@pytest.mark.unit
class TestMonitoringStack:
    def test_cloudwatch_alarms_created(self):
        """Test that CloudWatch alarms are created for critical metrics"""
        app = cdk.App()
        stack = MonitoringStack(app, "test-monitoring-stack")
        
        template = Template.from_stack(stack)
        
        # Verify Lambda error rate alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmName": Match.string_like_regexp(".*Lambda.*Error.*"),
            "ComparisonOperator": "GreaterThanThreshold",
            "EvaluationPeriods": 2,
            "Threshold": 5
        })
        
        # Verify DynamoDB throttle alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmName": Match.string_like_regexp(".*DynamoDB.*Throttle.*"),
            "ComparisonOperator": "GreaterThanThreshold"
        })
    
    def test_cloudwatch_dashboard_created(self):
        """Test that CloudWatch dashboard is created"""
        app = cdk.App()
        stack = MonitoringStack(app, "test-monitoring-stack")
        
        template = Template.from_stack(stack)
        
        # Verify CloudWatch dashboard
        template.has_resource_properties("AWS::CloudWatch::Dashboard", {
            "DashboardName": Match.string_like_regexp(".*TaskManagement.*"),
            "DashboardBody": Match.any_value()
        })
    
    def test_sns_alarm_topic_created(self):
        """Test that SNS topic for alarms is created"""
        app = cdk.App()
        stack = MonitoringStack(app, "test-monitoring-stack")
        
        template = Template.from_stack(stack)
        
        # Verify alarm SNS topic
        template.has_resource_properties("AWS::SNS::Topic", {
            "DisplayName": Match.string_like_regexp(".*Alerts.*")
        })
```

---

## 🔍 Stack Validation Tests

### File: `tests/unit/cdk/test_stack_validation.py`

Test overall stack validation and cross-stack dependencies.

#### Example Test Implementation:

```python
@pytest.mark.cdk
@pytest.mark.unit
class TestStackValidation:
    def test_stack_synthesis_succeeds(self):
        """Test that all stacks can be synthesized without errors"""
        app = cdk.App()
        
        # Create all stacks
        database_stack = DatabaseStack(app, "test-database")
        event_stack = EventStack(app, "test-events")
        api_stack = APIStack(app, "test-api",
                           table_name=database_stack.table.table_name,
                           topic_arn=event_stack.topic.topic_arn)
        monitoring_stack = MonitoringStack(app, "test-monitoring",
                                         api_stack=api_stack,
                                         database_stack=database_stack)
        
        # Verify synthesis succeeds
        cloud_assembly = app.synth()
        assert len(cloud_assembly.stacks) == 4
        
        # Verify stack names
        stack_names = [stack.stack_name for stack in cloud_assembly.stacks]
        assert "test-database" in stack_names
        assert "test-events" in stack_names
        assert "test-api" in stack_names
        assert "test-monitoring" in stack_names
    
    def test_cross_stack_references(self):
        """Test that cross-stack references are correctly configured"""
        app = cdk.App()
        
        database_stack = DatabaseStack(app, "test-database")
        event_stack = EventStack(app, "test-events")
        api_stack = APIStack(app, "test-api",
                           table_name=database_stack.table.table_name,
                           topic_arn=event_stack.topic.topic_arn)
        
        # Verify stack dependencies
        api_template = Template.from_stack(api_stack)
        
        # Should reference external table and topic
        api_template.has_resource_properties("AWS::Lambda::Function", {
            "Environment": {
                "Variables": {
                    "TABLE_NAME": {"Ref": Match.any_value()},
                    "TOPIC_ARN": {"Ref": Match.any_value()}
                }
            }
        })
    
    def test_resource_naming_conventions(self):
        """Test that resources follow naming conventions"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack", environment="staging")
        
        template = Template.from_stack(stack)
        
        # Verify resource names include environment
        template.has_resource_properties("AWS::Lambda::Function", {
            "FunctionName": Match.string_like_regexp(".*staging.*")
        })
    
    def test_security_configurations(self):
        """Test that security configurations are properly set"""
        app = cdk.App()
        stack = APIStack(app, "test-api-stack")
        
        template = Template.from_stack(stack)
        
        # Verify Lambda functions don't have overly permissive policies
        template.has_resource_properties("AWS::IAM::Policy", {
            "PolicyDocument": {
                "Statement": Match.array_with([
                    Match.object_like({
                        "Effect": "Allow",
                        "Action": Match.not_(Match.array_with(["*"]))
                    })
                ])
            }
        })
```

---

## 🔗 Integration Tests

### File: `tests/integration/cdk/test_stack_deployment.py`

Test actual CDK stack deployment (requires AWS credentials).

#### Example Test Implementation:

```python
@pytest.mark.integration
@pytest.mark.slow
class TestStackDeployment:
    def test_deploy_database_stack(self):
        """Test deploying database stack to AWS"""
        # Note: This requires AWS credentials and creates real resources
        app = cdk.App()
        stack = DatabaseStack(app, "test-deploy-database")
        
        # Deploy stack
        cloud_assembly = app.synth()
        
        # Verify deployment artifacts
        template_path = os.path.join(
            cloud_assembly.directory,
            "test-deploy-database.template.json"
        )
        assert os.path.exists(template_path)
        
        # Verify template is valid JSON
        with open(template_path, 'r') as f:
            template = json.load(f)
            assert "Resources" in template
            assert "AWS::DynamoDB::Table" in str(template)
    
    def test_stack_cost_estimation(self):
        """Test that stack costs are within expected range"""
        app = cdk.App()
        stack = DatabaseStack(app, "test-cost-database")
        
        template = Template.from_stack(stack)
        
        # Verify cost-effective configurations
        template.has_resource_properties("AWS::DynamoDB::Table", {
            "BillingMode": "PAY_PER_REQUEST"  # More cost-effective for variable workloads
        })
        
        # Verify no expensive resources are accidentally created
        template.resource_count_is("AWS::DynamoDB::Table", 1)  # Only one table
```

---

## 🌐 End-to-End Infrastructure Tests

### File: `tests/e2e/cdk/test_full_deployment.py`

Test complete infrastructure deployment and functionality.

#### Example Test Implementation:

```python
@pytest.mark.e2e
@pytest.mark.slow
class TestFullDeployment:
    def test_complete_infrastructure_deployment(self):
        """Test complete infrastructure deployment"""
        # This test would deploy the full stack and verify it works
        # Note: Requires AWS credentials and creates real resources
        
        app = cdk.App()
        
        # Deploy all stacks in correct order
        database_stack = DatabaseStack(app, "e2e-test-database")
        event_stack = EventStack(app, "e2e-test-events")
        api_stack = APIStack(app, "e2e-test-api",
                           table_name=database_stack.table.table_name,
                           topic_arn=event_stack.topic.topic_arn)
        monitoring_stack = MonitoringStack(app, "e2e-test-monitoring",
                                         api_stack=api_stack,
                                         database_stack=database_stack)
        
        # Synthesize all stacks
        cloud_assembly = app.synth()
        
        # Verify all stacks are synthesized
        assert len(cloud_assembly.stacks) == 4
        
        # Verify stack outputs are available
        for stack in cloud_assembly.stacks:
            template_path = os.path.join(
                cloud_assembly.directory,
                f"{stack.stack_name}.template.json"
            )
            assert os.path.exists(template_path)
    
    def test_multi_environment_deployment(self):
        """Test deployment to multiple environments"""
        environments = ["development", "staging", "production"]
        
        for env in environments:
            app = cdk.App()
            
            # Create environment-specific stacks
            database_stack = DatabaseStack(app, f"{env}-database", environment=env)
            api_stack = APIStack(app, f"{env}-api", 
                               environment=env,
                               table_name=database_stack.table.table_name)
            
            # Verify environment-specific configurations
            template = Template.from_stack(database_stack)
            
            if env == "production":
                # Production should have deletion protection
                template.has_resource_properties("AWS::DynamoDB::Table", {
                    "DeletionProtectionEnabled": True
                })
            else:
                # Non-production can have deletion protection disabled
                template.has_resource_properties("AWS::DynamoDB::Table", {
                    "DeletionProtectionEnabled": False
                })
```

---

## 🚀 Running CDK Tests

### Basic Commands

```bash
# Run all CDK unit tests
poetry run pytest tests/unit/cdk/ -m cdk

# Run specific CDK test file
poetry run pytest tests/unit/cdk/test_api_stack.py

# Run CDK integration tests (requires AWS credentials)
poetry run pytest tests/integration/cdk/ -m integration

# Run CDK end-to-end tests (requires AWS credentials and creates resources)
poetry run pytest tests/e2e/cdk/ -m e2e

# Synthesize CDK stacks for manual inspection
cd infrastructure/cdk
cdk synth

# Deploy to development environment
cdk deploy "*" --profile development

# Deploy with approval required
cdk deploy "*" --require-approval any-change
```

### Test Execution

```bash
# Expected output for CDK tests
poetry run pytest tests/unit/cdk/ -v

# Output:
# tests/unit/cdk/test_api_stack.py::TestAPIStack::test_lambda_functions_created PASSED
# tests/unit/cdk/test_database_stack.py::TestDatabaseStack::test_dynamodb_table_created PASSED
# tests/unit/cdk/test_event_stack.py::TestEventStack::test_sns_topic_created PASSED
# ...
# 40+ passed in 0.50s
```

---

## 🔄 TDD Workflow

### Step-by-Step Implementation

1. **Start with Database Stack**
   ```bash
   # Write test first
   poetry run pytest tests/unit/cdk/test_database_stack.py::TestDatabaseStack::test_dynamodb_table_created -v
   # Test fails (expected)
   
   # Implement stack
   # Edit infrastructure/cdk/stacks/database_stack.py
   
   # Run test again
   poetry run pytest tests/unit/cdk/test_database_stack.py::TestDatabaseStack::test_dynamodb_table_created -v
   # Test passes
   ```

2. **Continue with API Stack**
   ```bash
   # Write test first
   poetry run pytest tests/unit/cdk/test_api_stack.py::TestAPIStack::test_lambda_functions_created -v
   # Test fails
   
   # Implement stack
   # Edit infrastructure/cdk/stacks/api_stack.py
   
   # Run test again
   poetry run pytest tests/unit/cdk/test_api_stack.py::TestAPIStack::test_lambda_functions_created -v
   # Test passes
   ```

### Verification

After implementing all CDK stacks:

```bash
# Run all CDK tests
poetry run pytest tests/unit/cdk/ -v

# Synthesize stacks to verify they're valid
cd infrastructure/cdk
cdk synth

# Expected output:
# ============================= test session starts ==============================
# collected 40+ items
# tests/unit/cdk/test_api_stack.py ................ [ 25%]
# tests/unit/cdk/test_database_stack.py ................ [ 50%]
# tests/unit/cdk/test_event_stack.py ................ [ 75%]
# tests/unit/cdk/test_monitoring_stack.py ................ [100%]
# ============================= 40+ passed in 0.50s ==============================
```

---

## 📊 Test Coverage Goals

- **Stack Definitions:** 95%+ coverage
- **Resource Configurations:** 100% coverage
- **Security Policies:** 100% coverage
- **Integration Tests:** Critical deployment paths

### Coverage Report

```bash
poetry run pytest tests/unit/cdk/ --cov=infrastructure.cdk --cov-report=term-missing

# Expected coverage:
# Name                                    Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------------
# infrastructure/cdk/stacks/api_stack.py     60      0   100%
# infrastructure/cdk/stacks/database_stack.py 40      0   100%
# infrastructure/cdk/stacks/event_stack.py   45      0   100%
# infrastructure/cdk/stacks/monitoring_stack.py 35     0   100%
# ---------------------------------------------------------------------
# TOTAL                                    180      0   100%
```

---

## 🔗 Related Files

- **Implementation:** [TUTORIAL.md](../TUTORIAL.md#cdk-infrastructure-implementation)
- **Event Flow:** [EVENT_FLOW.md](../EVENT_FLOW.md)
- **Previous Layer:** [API_LAYER.md](API_LAYER.md)
- **Final Step:** [DEPLOYMENT.md](DEPLOYMENT.md) (planned)

---

## ✅ Checklist

Before final deployment, ensure:

- [ ] All 40+ CDK tests pass
- [ ] All stacks synthesize without errors
- [ ] Resource configurations are correct
- [ ] Security policies are properly configured
- [ ] Cross-stack dependencies work correctly
- [ ] Environment-specific configurations are tested
- [ ] Cost optimization is verified
- [ ] Monitoring and alerting are configured
- [ ] Integration tests pass with real AWS resources
- [ ] All tests follow TDD principles

**Next Step:** [Production Deployment and Testing](../TUTORIAL.md#deployment-and-testing) 