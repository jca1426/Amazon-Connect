pipeline {
    agent any

    environment {
        AWS_REGION = 'us-west-2'
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'
        LAMBDA_FUNCTION = 'OrderStatusFunc'
        FLOW_NAME = 'JCAtechco - Main Flow'
        FLOW_FILE = 'main.json'
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
                    rm -rf package

                    if [ ! -f import-json.py ]; then
                        echo "❌ import-json.py not found"
                        exit 1
                    fi

                    echo "Found Lambda function: import-json.py"
                    zip function.zip import-json.py

                    echo ""
                    echo "=== Package Contents ==="
                    unzip -l function.zip | head -20

                    echo ""
                    echo "=== Package Size ==="
                    ls -lh function.zip
                '''
            }
        }

        stage('Deploy to Lambda') {
            steps {
                withCredentials([
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]
                ]) {
                    sh '''
                        echo "=== Deploying to AWS Lambda ==="
                        echo "Function: ${LAMBDA_FUNCTION}"
                        echo "Region: ${AWS_REGION}"
                        echo ""

                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION} \
                          --output json \
                          --no-cli-pager > /dev/null

                        echo "Waiting for Lambda update to complete..."

                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION} \
                          --no-cli-pager

                        echo "✅ Lambda deployed successfully!"
                    '''
                }
            }
        }

        stage('Deploy main.json to Amazon Connect') {
            steps {
                withCredentials([
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]
                ]) {
                    sh '''
                        echo "=== Deploying main.json to Amazon Connect ==="
                        echo "Instance ID: ${CONNECT_INSTANCE_ID}"
                        echo "Region: ${AWS_REGION}"
                        echo ""

                        command -v jq >/dev/null 2>&1 || {
                            echo "❌ jq is required but not installed"
                            exit 1
                        }

                        cd dev/flows

                        if [ ! -f "${FLOW_FILE}" ]; then
                            echo "❌ Flow file ${FLOW_FILE} not found"
                            exit 1
                        fi

                        echo "Flow Name: ${FLOW_NAME}"
                        echo ""

                        echo "Checking if flow exists in Amazon Connect..."
                        FLOW_ID=$(aws connect list-contact-flows \
                            --instance-id ${CONNECT_INSTANCE_ID} \
                            --region ${AWS_REGION} \
                            --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                            --output text)

                        FLOW_ID=$(echo "$FLOW_ID" | tr -d '[:space:]')

                        echo "Flow ID: ${FLOW_ID}"
                        echo ""

                        echo "Extracting flow Content..."
                        FLOW_CONTENT=$(jq -c '.Content' "${FLOW_FILE}")

                        if [ -z "$FLOW_CONTENT" ] || [ "$FLOW_CONTENT" = "null" ]; then
                            echo "❌ Flow Content is empty or invalid"
                            exit 1
                        fi

                        if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" = "None" ]; then
                            echo "Creating new contact flow..."

                            aws connect create-contact-flow \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --name "${FLOW_NAME}" \
                                --type CONTACT_FLOW \
                                --content "$FLOW_CONTENT" \
                                --region ${AWS_REGION} \
                                --output json \
                                --no-cli-pager > /dev/null

                            echo "✅ Contact flow created successfully!"
                        else
                            echo "Updating existing contact flow..."

                            aws connect update-contact-flow-content \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --contact-flow-id "$FLOW_ID" \
                                --content "$FLOW_CONTENT" \
                                --region ${AWS_REGION} \
                                --output json \
                                --no-cli-pager > /dev/null

                            echo "✅ Contact flow updated successfully!"
                        fi
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "🎉 DEPLOYMENT SUCCESSFUL"
        }
        failure {
            echo "❌ DEPLOYMENT FAILED"
            echo "Please review the logs above"
        }
        always {
            cleanWs()
        }
    }
}