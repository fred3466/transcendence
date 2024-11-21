#set -x
. .env

    docker stop `docker ps -qa` 
    docker rm `docker ps -qa`

    docker volume rm `docker volume ls -q`
    
    docker network rm `docker network ls -q`
    docker system prune -fa
    
    rm -fr /home/fbourgue/ftt/.data
    


