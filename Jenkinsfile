pipeline {
  agent any
  options {
    timestamps()
  }
  environment {
    DOCKER_BUILDKIT = '1'
    COMPOSE_DOCKER_CLI_BUILD = '1'
    // Set your Docker Hub namespace here or via Jenkins env
    DOCKERHUB_USER = credentials('dockerhub-username-only')
    IMAGE_TAG = ''
    // Optional deploy settings; set as Jenkins environment vars
    STAGING_HOST = ''
    STAGING_SSH_USER = ''
    STAGING_DIR = ''
  }
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Compute Version') {
      steps {
        script {
          env.IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          echo "Image tag (short SHA): ${env.IMAGE_TAG}"
        }
      }
    }
    stage('Docker Build') {
      steps {
        sh '''
          set -e
          echo "Building images under namespace: ${DOCKERHUB_USER}"
          export DOCKERHUB_USER=${DOCKERHUB_USER}
          docker compose build --pull
        '''
      }
    }
    stage('Start Stack For Smoke Tests') {
      steps {
        sh '''
          set -e
          export DOCKERHUB_USER=${DOCKERHUB_USER}
          # Start DB first and wait for healthy
          docker compose up -d mysql
          echo "Waiting for MySQL health..."
          for i in $(seq 1 60); do
            status=$(docker inspect --format='{{.State.Health.Status}}' $(docker compose ps -q mysql) || true)
            if [ "$status" = "healthy" ]; then
              echo "MySQL is healthy"
              break
            fi
            echo "MySQL not healthy yet ($i/60), sleeping 2s..."; sleep 2
          done
          # Start the rest of services
          docker compose up -d
        '''
      }
    }
    stage('Health Checks') {
      steps {
        sh '''
          set -e
          bash scripts/wait_for_http.sh http://localhost:5000/health 60
          bash scripts/wait_for_http.sh http://localhost:5001/health 60
          bash scripts/wait_for_http.sh http://localhost:5002/health 60
          bash scripts/wait_for_http.sh http://localhost:5003/health 60
          bash scripts/wait_for_http.sh http://localhost:5005/health 60
          bash scripts/wait_for_http.sh http://localhost:8081 60
        '''
      }
    }
    stage('Smoke Tests') {
      steps {
        sh '''
          set -e
          bash scripts/smoke_test.sh
        '''
      }
    }
    stage('Login to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''
            set -e
            echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
          '''
        }
      }
    }
    stage('Tag and Push Images') {
      steps {
        sh '''
          set -e
          ns=${DOCKERHUB_USER}
          tag=${IMAGE_TAG}
          images="product_service user_service order_service payment_service notification_service frontend"
          for img in $images; do
            docker tag "$ns/$img:latest" "$ns/$img:$tag"
          done
          docker compose push
          for img in $images; do
            docker push "$ns/$img:$tag"
          done
        '''
      }
    }
    stage('Deploy to Staging (optional)') {
      when {
        expression { return env.STAGING_HOST?.trim() && env.STAGING_SSH_USER?.trim() && env.STAGING_DIR?.trim() }
      }
      steps {
        sshagent (credentials: ['deploy-ssh']) {
          sh '''
            set -e
            echo "Deploying to ${STAGING_SSH_USER}@${STAGING_HOST}:${STAGING_DIR}"
            ssh -o StrictHostKeyChecking=no ${STAGING_SSH_USER}@${STAGING_HOST} \
              "set -e; cd ${STAGING_DIR}; export DOCKERHUB_USER=${DOCKERHUB_USER}; docker compose pull; docker compose up -d; docker compose ps"
          '''
        }
      }
    }
  }
  post {
    always {
      script {
        sh '''
          set +e
          docker compose down -v
          docker logout || true
        '''
      }
    }
    success {
      script {
        echo "Build and push succeeded for tag ${env.IMAGE_TAG}"
        // Optional: Jenkins configured Mailer/Email-ext
        emailext subject: "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}", to: env.NOTIFY_EMAIL ?: '', body: "Images pushed with tags: latest and ${env.IMAGE_TAG}"
      }
    }
    failure {
      script {
        echo "Build failed; notifying."
        emailext subject: "FAILURE: ${env.JOB_NAME} #${env.BUILD_NUMBER}", to: env.NOTIFY_EMAIL ?: '', body: "See Jenkins for logs. Commit: ${env.GIT_COMMIT}"
      }
    }
  }
}
