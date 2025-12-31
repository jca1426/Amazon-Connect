pipeline {
    agent any
    environment {
        AWS_REGION = 'us-west-2'
        LAMBDA_FUNCTION = 'import-json'  // AWS Lambda function name (no .py)
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'  // Update this UUID!
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/jca1426/Amazon-Connect.git'
                sh 'ls -la'  // Show what was checked out
            }
        }
        
        stage('Package Lambda') {
            steps {
                sh '''
                    echo "Packaging Lambda function..."
                    rm -f function.zip
                    
                    # Install Python dependencies if requirements.txt exists
                    if [ -f requirements.txt ]; then
                        echo "Installing Python dependencies..."
                        pip3 install -r requirements.txt -t . || true
                    fi
                    
                    # Zip everything (including import-json.py)
                    # Exclude git files, flows folder, and markdown files
                    zip -r function.zip . -x "*.git*" -x "flows/*" -x "*.md" -x "Jenkinsfile"
                    
                    echo "Package contents:"
                    unzip -l function.zip
                    
                    echo "Package size:"
                    ls -lh function.zip
                '''
            }
        }
        
        stage('Deploy to Lambda') {
            steps {
                withAWS(credentials: 'aws-credentials', region: env.AWS_REGION) {
                    sh """
                        echo "Deploying to Lambda function: ${LAMBDA_FUNCTION}"
                        
                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION}
                        
                        echo "Waiting for Lambda update to complete..."
                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION}
                        
                        echo "✓ Lambda function deployed successfully!"
                        
                        # Show Lambda details
                        aws lambda get-function \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION} \
                          --query 'Configuration.[FunctionName,Runtime,LastModified]' \
                          --output table
                    """
                }
            }
        }
        
        stage('Update Amazon Connect Flows') {
            when {
                expression { fileExists('flows/') }
            }
            steps {
                withAWS(credentials: 'aws-credentials', region: env.AWS_REGION) {
                    sh '''
                        echo "Processing Contact Flows..."
                        
                        # Check if jq is installed
                        if ! command -v jq &> /dev/null; then
                            echo "ERROR: jq is not installed"
                            echo "Install with: brew install jq"
                            exit 1
                        fi
                        
                        # Process each JSON file in flows folder
                        cd flows
                        for flow_file in *.json; do
                            [ -f "$flow_file" ] || continue
                            
                            echo ""
                            echo "========================================"
                            echo "Processing: $flow_file"
                            echo "========================================"
                            
                            # Extract flow name from JSON
                            FLOW_NAME=$(jq -r '.Name // .name // empty' "$flow_file")
                            
                            if [ -z "$FLOW_NAME" ]; then
                                echo "⚠️  WARNING: Could not extract flow name from $flow_file"
                                echo "Skipping this file..."
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
                            
                            # Extract the flow content
                            FLOW_CONTENT=$(jq -c '.Content // .' "$flow_file")
                            
                            if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" == "None" ]; then
                                echo "Flow does not exist. Creating new flow..."
                                RESULT=$(aws connect create-contact-flow \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --name "$FLOW_NAME" \
                                  --type CONTACT_FLOW \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION} 2>&1)
                                
                                if [ $? -eq 0 ]; then
                                    NEW_FLOW_ID=$(echo "$RESULT" | jq -r '.ContactFlowId')
                                    echo "✓ SUCCESS: Created flow with ID: $NEW_FLOW_ID"
                                else
                                    echo "✗ ERROR: Failed to create flow"
                                    echo "$RESULT"
                                fi
                            else
                                echo "Flow exists with ID: $FLOW_ID"
                                echo "Updating flow content..."
                                RESULT=$(aws connect update-contact-flow-content \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --contact-flow-id "$FLOW_ID" \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION} 2>&1)
                                
                                if [ $? -eq 0 ]; then
                                    echo "✓ SUCCESS: Updated flow"
                                else
                                    echo "✗ ERROR: Failed to update flow"
                                    echo "$RESULT"
                                fi
                            fi
                            
                            echo "========================================"
                        done
                        
                        echo ""
                        echo "✓ All contact flows processed!"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 ✓ Pipeline completed successfully!'
            echo 'Lambda function and Contact Flows have been deployed.'
        }
        failure {
            echo '❌ Pipeline failed. Please check the logs above for details.'
        }
        always {
            cleanWs()
        }
    }
}