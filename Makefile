# Makefile da Micro-API de Tarefas.
# Alvos em inglês; textos de ajuda em português.
# Receitas de um comando só e sem sintaxe específica de shell (sh ou cmd).

ifeq ($(OS),Windows_NT)
PY := .venv/Scripts/python.exe
BOOT := python
else
PY := .venv/bin/python
BOOT := python3
endif

.PHONY: help install run test format

help:
	@echo Alvos disponiveis:
	@echo   make install  - cria o .venv se faltar e instala o requirements.txt
	@echo   make run      - sobe a API em http://127.0.0.1:8000 com recarga automatica
	@echo   make test     - roda os testes e falha se a cobertura ficar abaixo de 80 por cento
	@echo   make format   - formata app e tests com o black

install: .venv/pyvenv.cfg
	$(PY) -m pip install -r requirements.txt

.venv/pyvenv.cfg:
	$(BOOT) -m venv .venv

run:
	$(PY) -m uvicorn app.main:app --reload

test:
	$(PY) -m pytest --cov=app --cov-fail-under=80

format:
	$(PY) -m black app tests
