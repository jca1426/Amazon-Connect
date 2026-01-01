pipeline {
    agent any

    environment {
        AWS_REGION = 'us-west-2'
        LAMBDA_FUNCTION = 'OrderStatusFunc'
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'
        PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/sbin:${env.PATH}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'feature/aws-deploy',
                    url: 'https://github.com/jca1426/Amazon-Connect.git'

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
                        echo "❌ ERROR: import-json.py not found!"
                        exit 1
                    fi

                    echo "Found Lambda function: import-json.py"

                    if [ -f requirements.txt ]; then
                        echo "Installing Python dependencies..."
                        pip3 install -r requirements.txt -t ./package
                    fi

                    echo "Creating deployment package..."
                    zip function.zip import-json.py

                    if [ -d package ]; then
                        cd package && zip -r ../function.zip . && cd ..
                    fi

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
                          --no-cli-pager

                        echo "Waiting for Lambda to finish updating..."
                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION}

                        echo ""
                        aws lambda get-function-configuration \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION} \
                          --output table \
                          --query '{Name:FunctionName,Runtime:Runtime,Modified:LastModified,Size:CodeSize}'

                        echo ""
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

                        if ! command -v jq &> /dev/null; then
                            echo "❌ ERROR: jq is not installed!"
                            exit 1
                        fi

                        cd dev/flows

                        FLOW_FILE="main.json"
                        FLOW_NAME="JCAtechco - Main Flow"

                        if [ ! -f "$FLOW_FILE" ]; then
                            echo "❌ ERROR: main.json not found!"
                            exit 1
                        fi

                        echo "Flow Name: $FLOW_NAME"
                        echo ""

                        echo "Checking if flow exists..."
                        FLOW_ID=$(aws connect list-contact-flows \
                            --instance-id ${CONNECT_INSTANCE_ID} \
                            --region ${AWS_REGION} \
                            --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                            --output text)

                        FLOW_ID=$(echo "$FLOW_ID" | tr -d '[:space:]')
                        echo "Flow ID: $FLOW_ID"
                        echo ""

                        echo "Extracting .Content only (required by Amazon Connect)..."
                        jq -c '.Content' "$FLOW_FILE" > /tmp/flow_content.json

                        if [ ! -s /tmp/flow_content.json ]; then
                            echo "❌ ERROR: Flow content is empty!"
                            exit 1
                        fi

                        if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" = "None" ]; then
                            echo "Creating new contact flow..."

                            aws connect create-contact-flow \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --name "$FLOW_NAME" \
                                --type CONTACT_FLOW \
                                --content file:///tmp/flow_content.json \
                                --region ${AWS_REGION} \
                                --no-cli-pager

                            echo "✅ Flow created successfully!"
                        else
                            echo "Updating existing contact flow..."

                            aws connect update-contact-flow-content \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --contact-flow-id "$FLOW_ID" \
                                --content file:///tmp/flow_content.json \
                                --region ${AWS_REGION} \
                                --no-cli-pager

                            echo "✅ Flow updated successfully!"
                        fi

                        rm -f /tmp/flow_content.json
                        echo ""
                        echo "✅ main.json deployed to Amazon Connect!"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '🎉 DEPLOYMENT COMPLETED SUCCESSFULLY'
            echo '✅ Lambda updated'
            echo '✅ Amazon Connect Main Flow deployed'
        }
        failure {
            echo '❌ DEPLOYMENT FAILED'
            echo 'Please review the logs above'
        }
        always {
            cleanWs()
        }
    }
}
