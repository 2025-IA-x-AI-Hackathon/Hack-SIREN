.PHONY: help build up down restart logs clean wait-for-services run-preprocessing run-hybrid-rag run-scripts setup

help: ## 도움말 표시
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

build: ## Docker 이미지 빌드
	docker compose build

up: ## 서비스 시작 (detached)
	docker compose up -d

down: ## 서비스 중지
	docker compose down

restart: ## 서비스 재시작
	docker compose restart

logs: ## 모든 서비스 로그 확인
	docker compose logs -f

logs-api: ## API 서비스 로그 확인
	docker compose logs -f api

logs-neo4j: ## Neo4j 서비스 로그 확인
	docker compose logs -f neo4j

logs-chroma: ## Chroma 서비스 로그 확인
	docker compose logs -f chroma

clean: ## 모든 컨테이너 및 볼륨 삭제 (주의: 데이터 삭제됨)
	docker compose down -v
	docker system prune -f

ps: ## 실행 중인 서비스 확인
	docker compose ps

shell-api: ## API 컨테이너 쉘 접속
	docker compose exec api /bin/bash

shell-neo4j: ## Neo4j 컨테이너 쉘 접속
	docker compose exec neo4j /bin/bash

shell-chroma: ## Chroma 컨테이너 쉘 접속
	docker compose exec chroma /bin/sh

wait-for-services: ## Docker 서비스가 준비될 때까지 대기
	@echo "========================================="
	@echo "Docker 서비스 준비 대기 중..."
	@echo "========================================="
	@cd .. && python3 scripts/wait_for_services.py || exit 1

run-preprocessing: wait-for-services ## preprocessing.py 실행
	@echo "========================================="
	@echo "preprocessing.py 실행 중..."
	@echo "========================================="
	@cd .. && python3 preprocessing.py || exit 1
	@echo "✓ preprocessing.py 실행 완료"

run-hybrid-rag: wait-for-services ## hybrid_rag_advanced.py 실행
	@echo "========================================="
	@echo "hybrid_rag_advanced.py 실행 중..."
	@echo "========================================="
	@cd .. && python3 hybrid_rag_advanced.py || exit 1
	@echo "✓ hybrid_rag_advanced.py 실행 완료"

run-scripts: run-preprocessing run-hybrid-rag ## 모든 스크립트 순차 실행 (preprocessing → hybrid_rag_advanced)
	@echo "========================================="
	@echo "모든 스크립트 실행 완료!"
	@echo "========================================="

setup: up wait-for-services run-scripts ## Docker 서비스 시작 및 모든 스크립트 실행 (원클릭 설정)
	@echo "========================================="
	@echo "완전한 설정 완료!"
	@echo "========================================="
	@echo "API: http://localhost:8000"
	@echo "Neo4j Browser: http://localhost:7474"
	@echo "Chroma: http://localhost:8001"

