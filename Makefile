.PHONY: install seed dev-backend dev-frontend test build

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	python backend/db/seed_loader.py

dev-backend:
	uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	pytest backend/tests/ -v

build:
	cd frontend && npm run build
