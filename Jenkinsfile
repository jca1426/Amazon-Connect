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
                        
                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION} \
                          --output text > /dev/null
                        
                        echo "Lambda code updated. Waiting for function to be ready..."
                        
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
                        
                        if ! command -v jq &> /dev/null; then
                            echo "❌ ERROR: jq is not installed!"
                            exit 1
                        fi
                        
                        cd dev/flows
                        
                        FLOW_FILE="order.json"
                        
                        if [ ! -f "$FLOW_FILE" ]; then
                            echo "❌ ERROR: order.json not found!"
                            exit 1
                        fi
                        
                        echo "========================================"
                        echo "📄 Processing: $FLOW_FILE"
                        echo "========================================"
                        
                        # Extract flow name
                        FLOW_NAME=$(jq -r '.Metadata.name // .name // .Name // empty' "$FLOW_FILE")
                        
                        if [ -z "$FLOW_NAME" ]; then
                            echo "❌ ERROR: Could not extract flow name"
                            exit 1
                        fi
                        
                        echo "Flow Name: $FLOW_NAME"
                        echo ""
                        
                        # Check if flow exists
                        echo "Checking if flow exists in Amazon Connect..."
                        FLOW_ID=$(aws connect list-contact-flows \
                            --instance-id ${CONNECT_INSTANCE_ID} \
                            --region ${AWS_REGION} \
                            --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                            --output text 2>&1)
                        
                        if [ $? -ne 0 ]; then
                            echo "❌ ERROR: Failed to list contact flows"
                            echo "Error: $FLOW_ID"
                            exit 1
                        fi
                        
                        FLOW_ID=$(echo "$FLOW_ID" | tr -d '[:space:]')
                        echo "Flow ID from Connect: $FLOW_ID"
                        echo ""
                        
                        # Save flow content to a temporary file (IMPORTANT FIX!)
                        jq -c '.' "$FLOW_FILE" > /tmp/flow_content.json
                        
                        if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" == "None" ]; then
                            echo "Creating new flow..."
                            
                            CREATE_RESULT=$(aws connect create-contact-flow \
                              --instance-id ${CONNECT_INSTANCE_ID} \
                              --name "$FLOW_NAME" \
                              --type CONTACT_FLOW \
                              --content file:///tmp/flow_content.json \
                              --region ${AWS_REGION} 2>&1)
                            
                            if [ $? -eq 0 ]; then
                                NEW_FLOW_ID=$(echo "$CREATE_RESULT" | jq -r '.ContactFlowId // .Id // empty' 2>/dev/null)
                                echo ""
                                echo "✅ SUCCESS: Created flow in Amazon Connect"
                                echo "   Flow Name: $FLOW_NAME"
                                echo "   Flow ID: $NEW_FLOW_ID"
                            else
                                echo ""
                                echo "❌ ERROR: Failed to create flow"
                                echo "$CREATE_RESULT"
                                exit 1
                            fi
                        else
                            echo "Flow exists. Updating flow content..."
                            
                            UPDATE_RESULT=$(aws connect update-contact-flow-content \
                              --instance-id ${CONNECT_INSTANCE_ID} \
                              --contact-flow-id "$FLOW_ID" \
                              --content file:///tmp/flow_content.json \
                              --region ${AWS_REGION} 2>&1)
                            
                            if [ $? -eq 0 ]; then
                                echo ""
                                echo "✅ SUCCESS: Updated flow in Amazon Connect"
                                echo "   Flow Name: $FLOW_NAME"
                                echo "   Flow ID: $FLOW_ID"
                            else
                                echo ""
                                echo "❌ ERROR: Failed to update flow"
                                echo "$UPDATE_RESULT"
                                exit 1
                            fi
                        fi
                        
                        # Clean up temp file
                        rm -f /tmp/flow_content.json
                        
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
            echo ''
            echo 'Summary:'
            echo '  ✅ Lambda function: OrderStatusFunc updated'
            echo '  ✅ Contact flow: JCATechCo - Order Status deployed to Amazon Connect'
            echo ''
            echo 'Your Contact Flow as Code pipeline is now working!'
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