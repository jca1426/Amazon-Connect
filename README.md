# Amazon Connect Contact Center Demo

A portfolio project demonstrating how to build a simple customer support contact center using **Amazon Connect** and improve it with **DevOps practices** such as version control, CI/CD, observability, security hardening, and cost controls.

---

# Overview

This project simulates a customer support contact center for **JCA Tech Company** with a main IVR menu that routes callers to:

- **Sales**
- **Technical Support**
- **Order Status**

The solution includes queue-based routing, business hours handling, an order status automation flow backed by AWS Lambda, and a DevOps-focused operating model for managing Amazon Connect safely and reliably.

---

# Demo Scope

## Main Call Flow

The main menu greets the caller and provides three routing options:

- Press **1** for **Sales**
- Press **2** for **Technical Support**
- Press **3** for **Order Status**

## Routing Design

- **Sales** available **24 hours**
- **Technical Support** available **Monday – Friday (9 AM – 5 PM)**
- **Order Status** handled via **automated response**

---

# Core Components Built

- Amazon Connect instance and admin setup
- Business hours configuration
- Sales and Technical Support queues
- Sales and Technical routing profiles
- Agent user creation
- Main contact flow
- Sales contact flow
- Technical Support contact flow
- Order Status flow
- Lambda function for order status automation
- Phone number configuration for inbound calls

---

# Architecture

## Services Used

- **Amazon Connect** – Cloud contact center platform
- **AWS Lambda** – Backend logic for order status retrieval
- **GitHub** – Version control
- **Jenkins** – CI/CD automation
- **Terraform** – Infrastructure provisioning
- **IAM** – Security and least-privilege access
- **Amazon S3** – Call recording storage and lifecycle policies

---

# High Level Flow

1. Customer calls the Amazon Connect phone number
2. Main IVR flow presents options
3. Caller selects Sales, Technical Support, or Order Status
4. Routing directs the call to the correct queue or Lambda automation
5. DevOps pipeline manages deployments and updates

---

# DevOps Improvements

This project extends a basic Amazon Connect implementation by introducing **six DevOps improvement pillars**.

---

## 1. Contact Flow as Code

Amazon Connect contact flows are exported as **JSON files** and stored in **GitHub**.

### Benefits

- Version control
- Change history
- Safe collaboration
- Easy rollback of broken changes

---

## 2. Time-Based Routing

Business hour logic is centralized into a reusable flow.

### Benefits

- Consistent handling of after-hours calls
- Easy updates to schedules or holidays
- Reduced duplication
- Better caller experience

---

## 3. Resilient Order Status Flow

Lambda integrations include:

- Timeout protection
- Retry limits
- Error handling
- Fallback routing

### Benefits

- Prevents automation failures from blocking calls
- Avoids dead-end experiences
- Maintains reliable customer service

---

## 4. Observability

Customer-centric monitoring was introduced.

### Metrics

- Queue wait time
- Call abandonment rate
- Lambda error rates
- ContactId-based tracing

### Benefits

- Faster incident investigation
- Operational visibility
- Data-driven improvements

---

## 5. Security & IAM Hardening

IAM roles are separated for:

- Amazon Connect
- AWS Lambda

### Benefits

- Least-privilege security
- Reduced blast radius
- Stronger access control

---

## 6. Cost Controls

Cost management includes:

- S3 lifecycle policies for call recordings
- Budget alerts

### Benefits

- Prevent unexpected AWS charges
- Manage data retention
- Improve financial governance

---

# CI/CD Pipeline

Deployment pipeline concept:

```
GitHub → Jenkins → AWS Lambda → Amazon Connect
```

This pipeline enables automated updates to:

- Lambda function code
- Amazon Connect contact flow JSON

---

# Terraform Extensions

The project also demonstrates Infrastructure as Code for:

- VPC deployment
- Subnets
- Route tables
- Network configuration
- EKS cluster deployment

---

# What I Learned

This project helped strengthen my knowledge in:

- Amazon Connect architecture
- IVR flow design
- AWS Lambda integration
- CI/CD pipelines
- Infrastructure as Code
- Cloud observability
- IAM security best practices
- Cost optimization strategies

---

# Suggested Repository Structure

```
amazon-connect-contact-center-demo
│
├── README.md
├── docs
│   └── presentation.pdf
│
├── flows
│   ├── main-flow.json
│   ├── sales-flow.json
│   ├── technical-flow.json
│   └── order-status-flow.json
│
├── lambda
│   └── order-status-function
│       └── lambda_function.py
│
├── jenkins
│   └── Jenkinsfile
│
├── terraform
│   ├── vpc
│   └── eks
│
└── images
    ├── architecture.png
    ├── contact-flow.png
    └── pipeline.png
```

---

# Future Improvements

Possible enhancements for this project:

- Automated Jenkins pipeline implementation
- CloudWatch dashboards and alerts
- Holiday calendar routing automation
- Terraform reusable modules
- Architecture diagrams
- Integration tests for Lambda functions

---

# Author

**John Carlos Arche**

---

# Portfolio Value

This project demonstrates practical experience combining:

- Cloud infrastructure
- Contact center architecture
- DevOps automation
- CI/CD
- Observability
- Security
- Cost management

It shows how customer-facing systems can be operated using modern **DevOps practices**.
