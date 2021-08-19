pipeline {
  agent 'any'

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
