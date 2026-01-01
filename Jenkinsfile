pipeline {
  agent any

  environment {
    AWS_REGION = 'us-west-2'
    CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'
    CONTACT_FLOW_NAME = 'JCAtechco - Main Flow'
    LAMBDA_FUNCTION_NAME = 'OrderStatusFunc'
    AWS_CLI = '/usr/local/bin/aws'
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          echo "=== Repository Structure ==="
          ls -la

          echo ""
          echo "=== Dev/Flows Contents ==="
          ls -la dev/flows/
        '''
      }
    }

    stage('Package Lambda') {
      steps {
        sh '''
          echo "=== Packaging Lambda Function ==="
          rm -f function.zip

          if [ ! -f import-json.py ]; then
            echo "❌ import-json.py not found"
            exit 1
          fi

          zip function.zip import-json.py
          ls -lh function.zip
        '''
      }
    }

    stage('Deploy to Lambda') {
      steps {
        withCredentials([[
          $class: 'AmazonWebServicesCredentialsBinding',
          credentialsId: 'aws-credentials'
        ]]) {
          sh '''
            set -e
            export AWS_DEFAULT_OUTPUT=json

            echo "AWS CLI version:"
            ${AWS_CLI} --version

            ${AWS_CLI} lambda update-function-code \
              --function-name ${LAMBDA_FUNCTION_NAME} \
              --zip-file fileb://function.zip \
              --region ${AWS_REGION} \
              --no-cli-pager

            ${AWS_CLI} lambda wait function-updated \
              --function-name ${LAMBDA_FUNCTION_NAME} \
              --region ${AWS_REGION}

            echo "✅ Lambda deployed successfully"
          '''
        }
      }
    }

    stage('Deploy main.json to Amazon Connect') {
      steps {
        withCredentials([[
          $class: 'AmazonWebServicesCredentialsBinding',
          credentialsId: 'aws-credentials'
        ]]) {
          sh '''
            set -e
            export AWS_DEFAULT_OUTPUT=json

            command -v jq

            cd dev/flows

            echo "=== Fetching Contact Flow ID ==="
            FLOW_ID=$(${AWS_CLI} connect list-contact-flows \
              --instance-id ${CONNECT_INSTANCE_ID} \
              --region ${AWS_REGION} \
              --query "ContactFlowSummaryList[?Name=='${CONTACT_FLOW_NAME}'].Id" \
              --output text | tr -d '[:space:]')

            if [ -z "$FLOW_ID" ]; then
              echo "❌ Contact Flow not found"
              exit 1
            fi

            echo "✔ Found Flow ID: $FLOW_ID"

            FLOW_CONTENT=$(jq -c . main.json)

            if [ -z "$FLOW_CONTENT" ] || [ "$FLOW_CONTENT" = "null" ]; then
              echo "❌ Invalid JSON content"
              exit 1
            fi

            ${AWS_CLI} connect update-contact-flow-content \
              --instance-id ${CONNECT_INSTANCE_ID} \
              --contact-flow-id "$FLOW_ID" \
              --content "$FLOW_CONTENT" \
              --region ${AWS_REGION}

            echo "✅ Amazon Connect flow updated successfully"
          '''
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
    success {
      echo '🎉 Pipeline completed successfully'
    }
    failure {
      echo '❌ Pipeline failed — check logs above'
    }
  }
}