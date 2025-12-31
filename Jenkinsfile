pipeline {
    agent any
    environment {
        AWS_REGION = 'us-west-2'
        LAMBDA_FUNCTION = 'OrderStatusFunc'
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'  // UPDATE THIS WITH YOUR REAL INSTANCE ID!
        PATH = "/usr/local/bin:/opt/homebrew/bin:${env.PATH}"
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
                    
                    # Clean up any old package
                    rm -f function.zip
                    rm -rf package
                    
                    # Verify Lambda file exists
                    if [ ! -f import-json.py ]; then
                        echo "ERROR: import-json.py not found in root directory!"
                        exit 1
                    fi
                    
                    echo "Found Lambda function: import-json.py"
                    
                    # Install Python dependencies if requirements.txt exists
                    if [ -f requirements.txt ]; then
                        echo "Installing Python dependencies..."
                        pip3 install -r requirements.txt -t ./package || true
                    fi
                    
                    # Create the deployment package
                    echo "Creating deployment package..."
                    zip function.zip import-json.py
                    
                    # Add dependencies if they were installed
                    if [ -d package ]; then
                        echo "Adding Python dependencies to package..."
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
                        
                        # Update Lambda function code
                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION}
                        
                        echo ""
                        echo "Waiting for Lambda function to be updated..."
                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION}
                        
                        echo ""
                        echo "=== Lambda Function Details ==="
                        aws lambda get-function \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION} \
                          --query 'Configuration.[FunctionName,Runtime,LastModified,CodeSize]' \
                          --output table
                        
                        echo ""
                        echo "✅ Lambda function deployed successfully!"
                    '''
                }
            }
        }
        
        stage('Update Amazon Connect Flows') {
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
                        echo "=== Processing Amazon Connect Contact Flows ==="
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
                        
                        # Count JSON files
                        FLOW_COUNT=$(ls -1 *.json 2>/dev/null | wc -l)
                        echo "Found ${FLOW_COUNT} contact flow(s) to process"
                        echo ""
                        
                        # Process each JSON file
                        for flow_file in *.json; do
                            # Skip if no files found
                            [ -f "$flow_file" ] || continue
                            
                            echo "========================================"
                            echo "📄 Processing: $flow_file"
                            echo "========================================"
                            
                            # Extract flow name from JSON
                            FLOW_NAME=$(jq -r '.Name // .name // empty' "$flow_file")
                            
                            if [ -z "$FLOW_NAME" ]; then
                                echo "⚠️  WARNING: Could not extract flow name from $flow_file"
                                echo "Skipping this file..."
                                echo ""
                                continue
                            fi
                            
                            echo "Flow Name: $FLOW_NAME"
                            
                            # Check if flow already exists in Amazon Connect
                            echo "Checking if flow exists in Amazon Connect..."
                            FLOW_ID=$(aws connect list-contact-flows \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --region ${AWS_REGION} \
                                --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                                --output text 2>/dev/null | tr -d '[:space:]')
                            
                            # Extract the flow content (or use entire JSON if no Content field)
                            FLOW_CONTENT=$(jq -c '.Content // .' "$flow_file")
                            
                            if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" == "None" ]; then
                                echo "Flow does not exist. Creating new flow..."
                                
                                CREATE_RESULT=$(aws connect create-contact-flow \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --name "$FLOW_NAME" \
                                  --type CONTACT_FLOW \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION} 2>&1)
                                
                                if [ $? -eq 0 ]; then
                                    NEW_FLOW_ID=$(echo "$CREATE_RESULT" | jq -r '.ContactFlowId // .Id // empty')
                                    echo "✅ SUCCESS: Created flow"
                                    echo "   Flow ID: $NEW_FLOW_ID"
                                else
                                    echo "❌ ERROR: Failed to create flow"
                                    echo "   Error: $CREATE_RESULT"
                                fi
                            else
                                echo "Flow exists with ID: $FLOW_ID"
                                echo "Updating flow content..."
                                
                                UPDATE_RESULT=$(aws connect update-contact-flow-content \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --contact-flow-id "$FLOW_ID" \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION} 2>&1)
                                
                                if [ $? -eq 0 ]; then
                                    echo "✅ SUCCESS: Updated flow"
                                else
                                    echo "❌ ERROR: Failed to update flow"
                                    echo "   Error: $UPDATE_RESULT"
                                fi
                            fi
                            
                            echo "========================================"
                            echo ""
                        done
                        
                        echo "✅ All contact flows processed successfully!"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 ✅ DEPLOYMENT COMPLETED SUCCESSFULLY!'
            echo 'Lambda function and Contact Flows have been deployed to AWS.'
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