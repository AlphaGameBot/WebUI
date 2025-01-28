pipeline {
    agent {
        docker {
            image 'boisvert/python-build'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    environment {
        BOT_TOKEN = credentials('alphagamebot-token')
        DISCORD_CLIENT_ID = 946533554953809930
        DISCORD_CLIENT_SECRET = credentials('alphagamebot-client-secret')
        DOCKER_TOKEN = credentials('alphagamedev-docker-token')
        AGB_VERSION = sh(returnStdout: true, script: "cat webui.json | jq '.VERSION' -cMr").trim()
        COMMIT_MESSAGE = sh(script: 'git log -1 --pretty=%B ${GIT_COMMIT}', returnStdout: true).trim()

        // MySQL stuff
        MYSQL_HOST = "hubby.internal"
        MYSQL_DATABASE = "alphagamebot"
        MYSQL_USER = "alphagamebot" 
        MYSQL_PASSWORD = credentials('alphagamebot-mysql-password')

        DOCKER_IMAGE = "alphagamedev/alphagamebot:webui-$AGB_VERSION"
    }
    stages {
        stage('build') {
            steps {
                // debug if necessary
                // sh 'printenv'

                echo "Building"
                // 8/1/2024 -> No Cache was added because of the fact that Pycord will never update :/
                // ----------> If you know a better way, please make a pull request!
                sh 'docker build -t $DOCKER_IMAGE \
                                --build-arg COMMIT_MESSAGE="$COMMIT_MESSAGE" \
                                --build-arg BUILD_NUMBER="$BUILD_NuiUMBER" \
                                --build-arg BRANCH_NAME="$BRANCH_NAME" \
                                --no-cache .'

            }
        }
        stage('push') {
            when { 
                // We ONLY want to push Docker images when we are in the master branch!
                branch 'master'
            }
            steps {
                echo "Pushing image to Docker Hub"
                sh 'echo $DOCKER_TOKEN | docker login -u alphagamedev --password-stdin'
                sh 'docker tag  $DOCKER_IMAGE alphagamedev/alphagamebot:webui-latest' // point tag latest to most recent version
                sh 'docker push $DOCKER_IMAGE' // push tag latest version
                sh 'docker push alphagamedev/alphagamebot:webui-latest' // push tag latest
                sh 'docker logout'
            }
        }
        stage('deploy') {
            steps {
                // conditionally deploy
                sh "docker container stop alphagamebot-webui || true"
                sh "docker container rm alphagamebot-webui || true"
                sh "docker run -d \
                                --name alphagamebot-webui \
                                -e BOT_TOKEN -e BUILD_NUMBER -e DISCORD_CLIENT_ID -e DISCORD_CLIENT_SECRET \
                                -e MYSQL_HOST -e MYSQL_DATABASE -e MYSQL_USER -e MYSQL_PASSWORD \
                                -e GIT_COMMIT --restart=always -p  5600:5000 \
                                $DOCKER_IMAGE" flask run -h 0.0.0.0
            }
        }
    } // stages
}
