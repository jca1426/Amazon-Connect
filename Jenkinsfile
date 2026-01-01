pipeline {
    agent any

    environment {
        AWS_REGION = 'us-west-2'
        CONNECT_INSTANCE_ID = '5b494e85-ab6a-45ca-94f5-5e645ee1a7e3'
        LAMBDA_FUNCTION = 'OrderStatusFunc'
        FLOW_NAME = 'JCAtechco - Main Flow'
        FLOW_FILE = 'main.json'

        PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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
                withCredentials([
                    [
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: 'aws-credentials',
                        accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                        secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                    ]
                ]) {
                    sh '''
                        # 🔒 HARD FIX: override poisoned Jenkins env
                        export AWS_DEFAULT_OUTPUT=json

                        aws --version

                        aws lambda update-function-code \
                          --function-name "${LAMBDA_FUNCTION}" \
                          --zip-file fileb://function.zip \
                          --region "${AWS_REGION}" \
                          --no-cli-pager > /dev/null

                        aws lambda wait function-updated \
                          --function-name "${LAMBDA_FUNCTION}" \
                          --region "${AWS_REGION}"

                        echo "✅ Lambda deployed successfully"
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
                        export AWS_DEFAULT_OUTPUT=json

                        command -v jq >/dev/null || exit 1
                        command -v aws >/dev/null || exit 1

                        cd dev/flows

                        FLOW_ID=$(aws connect list-contact-flows \
                          --instance-id "${CONNECT_INSTANCE_ID}" \
                          --region "${AWS_REGION}" \
                          --query "ContactFlowSummaryList[?Name=='${FLOW_NAME}'].Id" \
                          --output text)

                        FLOW_ID=$(echo "$FLOW_ID" | tr -d '[:space:]')
                        FLOW_CONTENT=$(jq -c '.Content' "${FLOW_FILE}")

                        if [ -z "$FLOW_CONTENT" ] || [ "$FLOW_CONTENT" = "null" ]; then
                            echo "❌ Invalid flow content"
                            exit 1
                        fi

                        if [ -z "$FLOW_ID" ] || [ "$FLOW_ID" = "None" ]; then
                            aws connect create-contact-flow \
                              --instance-id "${CONNECT_INSTANCE_ID}" \
                              --name "${FLOW_NAME}" \
                              --type CONTACT_FLOW \
                              --content "$FLOW_CONTENT" \
                              --region "${AWS_REGION}"
                        else
                            aws connect update-contact-flow-content \
                              --instance-id "${CONNECT_INSTANCE_ID}" \
                              --contact-flow-id "$FLOW_ID" \
                              --content "$FLOW_CONTENT" \
                              --region "${AWS_REGION}"
                        fi

                        echo "✅ Contact flow deployed successfully"
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}