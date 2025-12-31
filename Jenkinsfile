pipeline {
    agent any
    environment {
        AWS_CREDS = credentials('aws-credentials')
        AWS_REGION = 'us-west-2'
        LAMBDA_FUNCTION = 'import-json'  // Remove the .py. extension
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3' // Your actual instance ID
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/jca1426/Amazon-Connect.git'
            }
        }
        
        stage('Package Lambda') {
            steps {
                script {
                    // Clean previous builds
                    sh 'rm -f function.zip'
                    
                    // Package Lambda function
                    sh '''
                        if [ -f requirements.txt ]; then
                            pip install -r requirements.txt -t .
                        fi
                        zip -r function.zip . -x "*.git*" -x "flows/*" -x "*.md"
                    '''
                }
            }
        }
        
        stage('Deploy to Lambda') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', 
                                  credentialsId: 'aws-credentials']]) {
                    sh """
                        aws lambda update-function-code \
                          --function-name ${LAMBDA_FUNCTION} \
                          --zip-file fileb://function.zip \
                          --region ${AWS_REGION}
                        
                        # Wait for Lambda to be updated
                        aws lambda wait function-updated \
                          --function-name ${LAMBDA_FUNCTION} \
                          --region ${AWS_REGION}
                    """
                }
            }
        }
        
        stage('Update Amazon Connect Flows') {
            when {
                expression { fileExists('flows/') }
            }
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', 
                                  credentialsId: 'aws-credentials']]) {
                    sh '''
                        for flow in flows/*.json; do
                            if [ ! -f "$flow" ]; then
                                echo "No flow files found"
                                continue
                            fi
                            
                            echo "Processing flow: $flow"
                            
                            # Extract flow name from JSON
                            FLOW_NAME=$(jq -r '.Name // .name // empty' "$flow")
                            
                            if [ -z "$FLOW_NAME" ]; then
                                echo "Warning: Could not extract name from $flow, skipping"
                                continue
                            fi
                            
                            echo "Flow name: $FLOW_NAME"
                            
                            # Check if flow exists
                            FLOW_ID=$(aws connect list-contact-flows \
                                --instance-id ${CONNECT_INSTANCE_ID} \
                                --region ${AWS_REGION} \
                                --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                                --output text || echo "")
                            
                            # Extract content (the actual flow definition)
                            FLOW_CONTENT=$(jq -c '.Content // .' "$flow")
                            
                            if [ -z "$FLOW_ID" ]; then
                                echo "Creating new flow: $FLOW_NAME"
                                aws connect create-contact-flow \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --name "$FLOW_NAME" \
                                  --type CONTACT_FLOW \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION}
                            else
                                echo "Updating existing flow: $FLOW_NAME (ID: $FLOW_ID)"
                                aws connect update-contact-flow-content \
                                  --instance-id ${CONNECT_INSTANCE_ID} \
                                  --contact-flow-id $FLOW_ID \
                                  --content "$FLOW_CONTENT" \
                                  --region ${AWS_REGION}
                            fi
                            
                            echo "Successfully processed: $FLOW_NAME"
                        done
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed. Check the logs above.'
        }
        always {
            cleanWs()
        }
    }
}