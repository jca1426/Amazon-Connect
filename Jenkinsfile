pipeline {
    agent any

    environment {
        AWS_CREDS = credentials('aws-credentials') // ID of Jenkins AWS credentials
        AWS_REGION = 'us-west-2'                  // Change to your region
        LAMBDA_FUNCTION = 'import-json.py.'   // Name of your Lambda
        CONNECT_INSTANCE_ID = '292335388446' // Amazon Connect instance
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/jca1426/Amazon-Connect.git'
            }
        }

        stage('Package Lambda') {
            steps {
                // If your Lambda is already ready, just zip it
                sh 'zip -r function.zip .'
            }
        }

        stage('Deploy to Lambda') {
            steps {
                sh """
                export AWS_ACCESS_KEY_ID=${AWS_CREDS_USR}
                export AWS_SECRET_ACCESS_KEY=${AWS_CREDS_PSW}
                aws lambda update-function-code \
                  --function-name $LAMBDA_FUNCTION \
                  --zip-file fileb://function.zip \
                  --region $AWS_REGION
                """
            }
        }

        stage('Update Amazon Connect Flows') {
            when {
                expression { fileExists('flows/') } // Only if you have flow JSON files
            }
            steps {
                sh """
                export AWS_ACCESS_KEY_ID=${AWS_CREDS_USR}
                export AWS_SECRET_ACCESS_KEY=${AWS_CREDS_PSW}

                for flow in flows/*.json; do
                  FLOW_NAME=$(jq -r '.Name' $flow)
                  FLOW_ID=$(aws connect list-contact-flows \
                            --instance-id $CONNECT_INSTANCE_ID \
                            --query "ContactFlowSummaryList[?Name=='$FLOW_NAME'].Id" \
                            --output text \
                            --region $AWS_REGION)

                  if [ -z "$FLOW_ID" ]; then
                    # Create new flow if it doesn't exist
                    aws connect create-contact-flow \
                      --instance-id $CONNECT_INSTANCE_ID \
                      --name "$FLOW_NAME" \
                      --type CONTACT_FLOW \
                      --content file://$flow \
                      --region $AWS_REGION
                  else
                    # Update existing flow
                    aws connect update-contact-flow-content \
                      --instance-id $CONNECT_INSTANCE_ID \
                      --contact-flow-id $FLOW_ID \
                      --content file://$flow \
                      --region $AWS_REGION
                  fi
                done
                """
            }
        }
    }
}
