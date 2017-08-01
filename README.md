# youtube-dl-server-docker

Simply a Dockerized version of the wonderful `youtube-dl-api-server` package which is marketed as: 

> A REST API server for getting the info for videos from different sites, powered by youtube-dl.

Uses the latest version in `pip`.


## Usage
 
In your `docker-compose.yml` add: 

```yaml
  youtube-dl:
    image: 'mariozig/youtube-dl_server'
    ports:
        - '9191:9191'
 ```
 
 The server will be running at `http://0.0.0.0:9191/`.
 
