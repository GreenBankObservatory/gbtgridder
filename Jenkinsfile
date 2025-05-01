#!groovy

def schedule = env.BRANCH_NAME == 'master'       ? '@weekly' :
               env.BRANCH_NAME == 'release_3.0'  ? "@weekly" : ''


pipeline {
  agent {label 'rhel8'}

  triggers {
    // trigger builds per schedule
    cron(schedule)
  }

  environment {
    PATH = "/home/gbors/pythonversions/3.8/bin:${PATH}"
  }

  stages {
    stage('Init') {
      steps {
        lastChanges(
          since: 'LAST_SUCCESSFUL_BUILD',
          format:'SIDE',
          matching: 'LINE'
        )
      }
    }

    stage('virtualenv') {
      steps {
        sh '''
          ~gbosdd/pythonversions/3.9/bin/python -m venv jenkins-gridder-env
          source jenkins-gridder-env/bin/activate
          pip install -U pip setuptools wheel build
          pip install pytest
          python -m pip install "gbtgridder @ git+https://github.com/GreenBankObservatory/gbtgridder.git@master"
        '''
      }
    }

    stage('UnitTest') {
      steps {
        sh '''
        source jenkins-gridder-env/bin/activate
          ./RunAllUnitTests
        '''
      }
    }
    stage('IntegrationTest') {
      steps {
        sh '''
        source jenkins-gridder-env/bin/activate
          ./RunAllIntegrationTests
        '''
      }
    }
  }

  post {
    always {
      do_notify()
    }
  }
}
