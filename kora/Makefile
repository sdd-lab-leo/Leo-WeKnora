.PHONY: install run backend frontend seed test-smoke

install:
	python3 -m pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

run:
	@echo "Start backend: make backend"
	@echo "Start frontend: make frontend"

seed:
	cd backend && PYTHONPATH=. python3 ../scripts/seed_samples.py

test-smoke:
	cd backend && PYTHONPATH=. python3 ../scripts/smoke_test.py
