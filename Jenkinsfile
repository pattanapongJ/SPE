pipeline {
    agent any
    environment {
        VPN = credentials('fortinet-user')
    }
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'master', url: 'https://github.com/pattanapongJ/SPE.git'
            }
        }
        stage('Connect VPN') {
            steps {
                sh '''
                /usr/local/bin/vpn-connect.expect $VPN_USR $VPN_PSW spevpn &
                sleep 15
                '''
            }
        }
        stage('Deploy Locally') {
            steps {
                sh '''
                    cd /home/odoo/modules
                    git pull origin master
                    systemctl restart odoo
                '''
            }
        }
        stage('Disconnect VPN') {
            steps {
                sh 'forticlient vpn disconnect spevpn || true'
            }
        }
    }
}
