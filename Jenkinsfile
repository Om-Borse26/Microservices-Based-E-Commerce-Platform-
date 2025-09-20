pipeline {
  agent any
  options {
    timestamps()
  }
  parameters {
    booleanParam(name: 'DRY_RUN', defaultValue: false, description: 'If true, only print planned actions without building/pushing')
    booleanParam(name: 'RUN_TESTS', defaultValue: false, description: 'Run local stack and health checks (Windows agents skip by default)')
  }
  triggers {
    pollSCM('* * * * *')
  }
  environment {
    DOCKER_BUILDKIT = '1'
    COMPOSE_DOCKER_CLI_BUILD = '1'
    // Set your Docker Hub namespace here or via Jenkins env
    DOCKERHUB_USER = credentials('dockerhub-username-only')
    IMAGE_TAG = ''
  // Notifications
  NOTIFY_EMAIL = "omborse1618@gmail.com"
  // Optional deploy settings; set as Jenkins environment vars
    STAGING_HOST = ''
    STAGING_SSH_USER = ''
    STAGING_DIR = ''
  }
  stages {
    stage('Detect Changed Services') {
      steps {
        script {
          def base = ''
          // Try to find previous commit to diff against; if none, build all
          try {
            base = bat(script: 'git rev-parse HEAD^', returnStdout: true).trim()
          } catch (ignored) {
            base = ''
          }
          def diffCmd = base ? "git diff --name-only ${base} HEAD" : 'git ls-files'
          def files = bat(script: diffCmd, returnStdout: true).trim()
          echo "Changed files:\n${files}"
          def services = [] as Set
          files.split(/\r?\n/).each { f ->
            if (f == null || f.trim() == '') return
            if (f.startsWith('Dockerfile.product') || f.contains('product_service.py')) services << 'product_service'
            if (f.startsWith('Dockerfile.user') || f.contains('user_service.py')) services << 'user_service'
            if (f.startsWith('Dockerfile.order') || f.contains('order_service.py')) services << 'order_service'
            if (f.startsWith('Dockerfile.payment') || f.contains('payment_service.py')) services << 'payment_service'
            if (f.startsWith('Dockerfile.notification') || f.contains('notification_service.py')) services << 'notification_service'
            if (f.startsWith('Dockerfile.frontend') || f.startsWith('frontend/')) services << 'frontend'
            if (f == 'docker-compose.yml' || f.startsWith('requirements.txt')) {
              services.addAll(['product_service','user_service','order_service','payment_service','notification_service','frontend'])
            }
          }
          env.CHANGED_SERVICES = services.join(' ')
          echo "CHANGED_SERVICES='${env.CHANGED_SERVICES}'"
          echo "DRY_RUN='${params.DRY_RUN}'"
        }
      }
    }
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Compute Version') {
      steps {
        script {
          def tagOut = bat(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          env.IMAGE_TAG = tagOut
          echo "Image tag (short SHA): ${env.IMAGE_TAG}"
        }
      }
    }
    stage('Docker Build') {
      steps {
        bat '''
          set ns=%DOCKERHUB_USER%
          set services=%CHANGED_SERVICES%
          echo Building images under namespace: %ns%
          if "%DRY_RUN%"=="true" (
            if "%services%"=="" (
              echo [DRY RUN] Would build all services
            ) else (
              echo [DRY RUN] Would build services: %services%
            )
          ) else (
            if "%services%"=="" (
              echo No specific service changes detected; building all.
              docker compose build --pull
            ) else (
              echo Building changed services: %services%
              for %%i in (%services%) do docker compose build --pull %%i
            )
          )
        '''
      }
    }
    stage('Start Stack For Smoke Tests') {
      when { expression { return params.RUN_TESTS } }
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
      when { expression { return params.RUN_TESTS } }
      steps {
                bat 'scripts\\wait_for_http.bat http://localhost:5000/health 60'
                bat 'scripts\\wait_for_http.bat http://localhost:5001/health 60'
                bat 'scripts\\wait_for_http.bat http://localhost:5002/health 60'
                bat 'scripts\\wait_for_http.bat http://localhost:5003/health 60'
                bat 'scripts\\wait_for_http.bat http://localhost:5005/health 60'
                bat 'scripts\\wait_for_http.bat http://localhost:8081 60'
      }
    }
    stage('Login to Docker Hub') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          bat '''
            echo Logging into Docker Hub as %DOCKERHUB_USERNAME%
            if "%DRY_RUN%"=="true" (
              echo [DRY RUN] Would docker login
            ) else (
              echo %DOCKERHUB_TOKEN%>tmp_pwd.txt
              docker login -u "%DOCKERHUB_USERNAME%" --password-stdin < tmp_pwd.txt
              del tmp_pwd.txt
            )
          '''
        }
      }
    }
    stage('Tag and Push Images') {
            steps {
                bat '''
                  set ns=%DOCKERHUB_USER%
                  set tag=%IMAGE_TAG%
                  set services=%CHANGED_SERVICES%
                  if "%services%"=="" (
                    set services=product_service user_service order_service payment_service notification_service frontend
                  )
                  if "%DRY_RUN%"=="true" (
                    echo [DRY RUN] Would tag services: %services% with tag %tag%
                    echo [DRY RUN] Would push latest for: %services%
                    if not "%tag%"=="" echo [DRY RUN] Would also push tag %tag% for: %services%
                  ) else (
                    for %%i in (%services%) do docker tag %ns%/%%i:latest %ns%/%%i:%tag%
                    if "%services%"=="product_service user_service order_service payment_service notification_service frontend" (
                      docker compose push
                    ) else (
                      for %%i in (%services%) do docker push %ns%/%%i:latest
                    )
                    if not "%tag%"=="" (
                      for %%i in (%services%) do docker push %ns%/%%i:%tag%
                    ) else (
                      echo Skipping tag push: IMAGE_TAG is empty
                    )
                  )
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
        bat '''
          if "%DRY_RUN%"=="true" (
            echo [DRY RUN] Would docker compose down -v and docker logout
          ) else (
            docker compose down -v
            docker logout
          )
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
