pipeline {
    agent any 

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/samals'                                   //<-----change this to your MiamiID!
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/Samals-sha/samals_255-lab5-1.git'     //<-----change this to match this new repository!
        KUBECONFIG = credentials('samals-225')                           //<-----change this to match your kubernetes credentials (MiamiID-225)! 
    }

    stages {
        stage('Code Checkout') {
            steps {
                cleanWs()
                checkout([$class: 'GitSCM', branches: [[name: '*/main']],
                          userRemoteConfigs: [[url: "${GITHUB_URL}"]]])
            }
        }

        stage('Lint HTML') {
            steps {
                sh 'npm install htmlhint --save-dev'
                sh 'npx htmlhint *.html'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${IMAGE_TAG}", "-f Dockerfile.build .")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${DOCKER_IMAGE}:${IMAGE_TAG}").push()
                    }
                }
            }
        }

        stage('Deploy to Dev Environment') {
            steps {
                script {
                    // This sets up the Kubernetes configuration using the specified KUBECONFIG
                    def kubeConfig = readFile(KUBECONFIG)
                    sh "kubectl delete --all deployments --namespace=default"
                    // This updates the deployment-dev.yaml to use the new image tag
                    sh "sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment-dev.yaml"
                    sh "kubectl apply -f deployment-dev.yaml"
                    sh "kubectl rollout status deployment/flask-dev-deployment --namespace=default --timeout=3m"
                }
            }
        }

        stage('Generate Test Data') {
    steps {
        script {
            def appPod = ''
            def appLabelValue = 'flask'               
            def appDeploymentName = 'flask-dev-deployment' 
            def appContainerName = 'flask'         
            def appNamespace = 'default'                 
            echo "Finding a Running pod with label app=${appLabelValue} in namespace ${appNamespace}..."
            timeout(time: 3, unit: 'MINUTES') {
                while (appPod == '') {
                    appPod = sh(script: "kubectl get pods -l app=${appLabelValue} --namespace=${appNamespace} -o jsonpath='{.items[?(@.status.phase==\"Running\")].metadata.name}'", returnStdout: true).trim().tokenize(' ')[0] ?: ''
                    if (appPod == '') {
                        echo "No Running pod found yet with label app=${appLabelValue}. Current matching pods:"
                        sh "kubectl get pods -l app=${appLabelValue} --namespace=${appNamespace}"
                        sleep 15
                    } else {
                        echo "Found potential running pod: ${appPod}"
                    }
                }
            }

            if (appPod) {
                echo "Target pod for data generation: ${appPod}"
                
                echo "Waiting for pod ${appPod} to be fully Ready..."
                sh "kubectl wait --for=condition=Ready pod/${appPod} --namespace=${appNamespace} --timeout=2m"
                
                echo "Executing data-gen.py in pod ${appPod}, container ${appContainerName}..."
                sh "kubectl exec ${appPod} --namespace=${appNamespace} --container ${appContainerName} -- python3 data-gen.py"
                echo "data-gen.py script executed."

                echo "Verifying data generation by querying DB in pod..."
                try {
                    def queryOutput = sh(script: "kubectl exec ${appPod} --namespace=${appNamespace} --container ${appContainerName} -- sqlite3 /nfs/demo.db \"SELECT COUNT(*) FROM contacts WHERE name LIKE 'Test Name %';\"", returnStdout: true).trim()
                    echo "Query for 'Test Name %' count returned: ${queryOutput}"
                    if (queryOutput == "10") {
                        echo "DB Verification successful: Found 10 'Test Name %' contacts."
                    } else {
                        echo "DB Verification WARNING: Expected 10 'Test Name %' contacts, found ${queryOutput}."
                    }
                } catch (Exception e) {
                    echo "Warning: Error during database verification query: ${e.getMessage()}"
                }
            } else {
                error "Failed to find a running pod with label app=${appLabelValue} in namespace ${appNamespace} for data generation after timeout."
            }
        }
    }
}

        stage("Run Acceptance Tests") {
            steps {
                script {
                    sh 'docker stop qa-tests || true'
                    sh 'docker rm qa-tests || true'
                    sh 'docker build -t qa-tests -f Dockerfile.test .'
                    sh 'docker run qa-tests'
                }
            }
        }

                stage ("Run Security Checks") {
            steps {
                //                                                                 ###change the IP address in this section to your cluster IP address!!!!####
                sh 'docker pull public.ecr.aws/portswigger/dastardly:latest'
                sh '''
                    docker run --user $(id -u) -v ${WORKSPACE}:${WORKSPACE}:rw \
                    -e BURP_START_URL=http://10.48.10.109 \
                    -e BURP_REPORT_FILE_PATH=${WORKSPACE}/dastardly-report.xml \
                    public.ecr.aws/portswigger/dastardly:latest
                '''
            }
        }
        
        stage('Remove Test Data') {
            steps {
                script {
                    // Run the python script to generate data to add to the database
                    def appPod = sh(script: "kubectl get pods -l app=flask -o jsonpath='{.items[0].metadata.name}'", returnStdout: true).trim()
                    sh "kubectl exec ${appPod} -- python3 data-clear.py"
                }
            }
        }
         
        stage('Check Kubernetes Cluster') {
            steps {
                script {
                    sh "kubectl get all"
                }
            }
        }
    }

    post {

        success {
            slackSend color: "good", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        }
        unstable {
            slackSend color: "warning", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        }
        failure {
            slackSend color: "danger", message: "Build Completed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
        }
    }
}
