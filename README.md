# backend

Install guide:

create .venv

`python3 -m venv .venv`

activate 

`source .venv/bin/activate`

install reqs

`pip install -r requirements.txt`

# Nginx setup:
```
server {
    listen 80;
    server_name api.orbitwatch.xyz;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

# systemd setup:
```
[Unit]
Description=Waitress Server for Flask API
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/project/venv/bin"
ExecStart=/path/to/your/project/venv/bin/waitress-serve --listen=127.0.0.1:5050 app:app

[Install]
WantedBy=multi-user.target
```
