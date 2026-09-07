# Created this Makefile so that I won't forget to run postgres before starting my django server (else, the server wouldn't start)
.PHONE: start-backend stop-backend access-shell restart-backend 


# Read PORT from .env.backend, default to 8000 if not found or empty
PORT := $(shell grep -E '^PORT=' .env.backend | cut -d= -f2)
PORT := $(if $(PORT),$(PORT),8000)



start-backend:
	@echo "Starting Django on port $(PORT)..."
	@docker run sg-postgres
	@cd ~/backend && uv run manage.py runserver


# access postgresql client/shell to verify output from the backend.  
access-shell:
	@uv run manage.py dbshell 




# stop the backend by stopping the postgresql container.
# It is said that Django sometimes spawns orphan background porcesses. So a Makefile command can ensure 
# - the port is not owned by any proces, 
# - a uniform intertface for everyone on the team to stop the server regardless of their OS 
# - automation: can chain commands together such as stopping the server, running migrations and retsrating it with a single command (make restart)
stop-backend:
	@echo "Stopping Djnago server on port $(PORT)..."
	@docker stop sg-postgres
	@-kill -9 $$(lsof -t -i:$(PORT)) 2>/dev/null || true



restart-backend: stop-backend start-backend