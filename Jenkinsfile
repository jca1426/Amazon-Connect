pipeline {
    agent any
    environment {
        AWS_REGION = 'us-west-2'
        LAMBDA_FUNCTION = 'OrderStatusFunc'
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'  // UPDATE THIS WITH YOUR REAL INSTANCE ID!
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
                        echo "ERROR: import-json.py not found!"
                        exit 1
                    fi
                    
                    echo "Found Lambda function: import-json.py"
                    
                    if [ -f requirements.txt ]; then
                        echo "Installing Python dependencies..."
                        pip3 install -r requirements.txt -t ./package || true
                    fi
                    
                    echo "Creating deployment package..."
                    zip function.zip import-json.py
                    
                    if [ -d package ]; then
                        echo "Adding Python dependencies..."
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
                        
                        # Update Lambda function code (suppress JSON output to avoid parsing issues)
                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION} \
                          --output text > /dev/null
                        
                        echo "Lambda code updated. Waiting for function to be ready..."
                        
                        # Wait for update to complete
                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION}
                        
                        echo ""
                        echo "=== Lambda Function Details ==="
                        aws lambda get-function-configuration \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION} \
                          --output table \
                          --query '{Name:FunctionName,Runtime:Runtime,Modified:LastModified,Size:CodeSize}'
                        
                        echo ""
                        echo "✅ Lambda function deployed successfully!"
                    '''
                }
            }
        }
        
        stage('Deploy order.json to Amazon Connect') {
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
                        echo "=== Deploying order.json to Amazon Connect ==="
                        echo "Instance ID: ${CONNECT_INSTANCE_ID}"
                        echo "Region: ${AWS_REGION}"
                        echo ""
                        
                        # Check if jq is installed
                        if ! command -v jq &> /dev/null; then
                            echo "❌ ERROR: jq is not installed!"
                            echo "Please install jq using: brew install jq"
                            exit 1
                        fi
                        
                        # Navigate to flows directory
                        cd dev/flows
                        
                        # Process order.json only
                        FLOW_FILE="order.json"
                        
                        if [ ! -f "$FLOW_FILE" ]; then
                            echo "❌ ERROR: order.json not found!"
                            exit 1
                        fi
                        
                        echo "========================================"
                        echo "📄 Processing: $FLOW_FILE"
                        echo "========================================"
                        
                        # Extract flow name from JSON
                        FLOW_NAME=$(jq -r '.Name // .name // empty' "$FLOW_FILE")
                        
                        if [ -z "$FLOW_NAME" ]; then
                            echo "❌ ERROR: Could not extract flow name from order.json"
                            echo "File contents:"
                            cat "$FLOW_FILE" | jq '.' || cat "$FLOW_FILE"
                            exit 1
                        fi
                        
                        echo "Flow Name: $FLOW_NAME"
                        echo ""
                        
                        # Check if flow already exists in Amazon Connect
                        echo "Checking if flow exists in Amazon Connect..."
                        FLOW_ID=$(aws connect list-contact-flows \
                            --instance-id ${CONNECT_INSTANCE_ID} \
                            --region ${AWS_REGION} \
                            --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                            --output text 2>&1 | tr -d '[:space:]')
                        
                        if [ $? -ne 0 ]; then
                            echo "❌ ERROR: Failed to list contact flows"
                            echo "Error: $FLOW_ID"
                            echo ""
                            echo "Please verify:"
                            echo "1. Your Connect Instance ID is correct: ${CONNECT_INSTANCE_ID}"
                            echo "2. Your AWS credentials have Connect permissions"
                            exit 1
                        fi
                        
                        echo "Flow ID from Connect: '$FLOW_ID'"
                        
                        # Extract the flow content
                        FLOW_CONTENT=$(jq -c '.Content // .' "$FLOW_FILE")
                        
                        if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" == "None" ] || [ "$FLOW_ID" == "" ]; then
                            echo ""
                            echo "Flow does not exist. Creating new flow..."
                            
                            CREATE_RESULT=$(aws connect create-contact-flow \
                              --instance-id ${CONNECT_INSTANCE_ID} \
                              --name "$FLOW_NAME" \
                              --type CONTACT_FLOW \
                              --content "$FLOW_CONTENT" \
                              --region ${AWS_REGION} 2>&1)
                            
                            if [ $? -eq 0 ]; then
                                NEW_FLOW_ID=$(echo "$CREATE_RESULT" | jq -r '.ContactFlowId // .Id // empty' 2>/dev/null)
                                echo "✅ SUCCESS: Created flow"
                                echo "   Flow Name: $FLOW_NAME"
                                echo "   Flow ID: $NEW_FLOW_ID"
                            else
                                echo "❌ ERROR: Failed to create flow"
                                echo "   Error: $CREATE_RESULT"
                                exit 1
                            fi
                        else
                            echo ""
                            echo "Flow exists with ID: $FLOW_ID"
                            echo "Updating flow content..."
                            
                            UPDATE_RESULT=$(aws connect update-contact-flow-content \
                              --instance-id ${CONNECT_INSTANCE_ID} \
                              --contact-flow-id "$FLOW_ID" \
                              --content "$FLOW_CONTENT" \
                              --region ${AWS_REGION} 2>&1)
                            
                            if [ $? -eq 0 ]; then
                                echo "✅ SUCCESS: Updated flow"
                                echo "   Flow Name: $FLOW_NAME"
                                echo "   Flow ID: $FLOW_ID"
                            else
                                echo "❌ ERROR: Failed to update flow"
                                echo "   Error: $UPDATE_RESULT"
                                exit 1
                            fi
                        fi
                        
                        echo "========================================"
                        echo ""
                        echo "✅ order.json deployed successfully to Amazon Connect!"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 ✅ DEPLOYMENT COMPLETED SUCCESSFULLY!'
            echo 'Lambda function updated and order.json deployed to Amazon Connect.'
        }
        failure {
            echo '❌ DEPLOYMENT FAILED'
            echo 'Please check the logs above for error details.'
        }
        always {
            cleanWs()
        }
    }
}