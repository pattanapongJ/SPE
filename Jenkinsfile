pipeline {
    agent any
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master', url: 'https://github.com/pattanapongJ/SPE.git'
            }
        }
        stage('Deploy') {
            steps {
                sh '''
                    /usr/bin/sudo -u odoo bash -c '
                    cd /home/odoo/modules &&
                    git pull origin master &&
                    '
                    /usr/bin/sudo systemctl restart odoo
                '''
            }
        }
    }
}
