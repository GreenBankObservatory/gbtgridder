pipeline {
  agent 'any'

  env {
    PATH = "/home/sandboxes/monctrl/venvs/pre-commit-env/bin:${PATH}"
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
        sh '''
          pre-commit run --all-files
        '''
      }
    }
  }

  post {
    always {
      do_notify(to: 'tchamber@nrao.edu')
    }
  }
}
