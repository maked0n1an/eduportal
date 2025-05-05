up() {
    docker compose -f src/docker-compose.yaml up -d
}

down() {
    docker compose -f src/docker-compose.yaml down 
    docker network prune --force
}


case "$1" in 
    "up")
        up
        ;;
    "down")
        down
        ;;
    *)
        echo "Usage: $0 {up|down}"
        exit 1
        ;;
esac