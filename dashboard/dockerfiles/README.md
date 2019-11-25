# Dashboard Dockerfile

This is an attempt to make the testing and deploying process for dashboard
more consistent and running everything in docker.

## Make Clean & Make

```
docker-compose run make
```

## Run Python Unit Tests

```
docker-compose run python-unittest
```

## Deply Dashboard

```
docker-compose run deploy
```

...and if not authedauthenticated

```
docker-compose run auto
```