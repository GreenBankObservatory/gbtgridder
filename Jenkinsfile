pipeline {
  agent 'any'

  environment {
    PATH = "/home/gbors/pythonversions/3.8/bin:${PATH}"
  }

  stages {
    stage('Init') {
      steps {
        lastChanges(
          since: 'PREVIOUS_REVISION',
          format:'SIDE',
          matching: 'LINE'
        )
      }
    }

    stage('pre-commit') {
      steps {
        sh """
          # Run only on changed files (if there is no previous commit, use the current one)
          pre-commit run --from-ref ${env.GIT_PREVIOUS_COMMIT != null ? env.GIT_PREVIOUS_COMMIT : env.GIT_COMMIT} --to-ref ${env.GIT_COMMIT}
        """
      }
    }
  }

  post {
    always {
      do_notify()
    }
  }
}
