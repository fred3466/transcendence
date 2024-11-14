Welcome to the `ft_transcendence` project!

## Overview

This project is built using Django LTS version.

## Requirements
- Make
- Docker
- docker-compose

## 42 API
Register a new app in the 42 API
>[!IMPORTANT]
> In the callback section put this url
>>```http:localhost:8000/users/callback```

## Environment Variables

Ensure you have the following environment variables set in your `.env` file:
> the `.env` file should be in the root folder

```env
POSTGRES_DB=example
POSTGRES_USER=example
POSTGRES_PASSWORD=example
POSTGRES_EMAIL=example
CLIENT_ID=#42 Api UID Key
CLIENT_SECRET=#42 Api Secret Key
```

## How to launch
```
cd %FOLDER_NAME%
make up/build
```


## Accessing Web Application

To access the web application, navigate to `http://localhost:8000` in your web browser.
# transcendence
# transcendence
