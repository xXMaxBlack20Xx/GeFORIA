@echo off
setlocal DisableDelayedExpansion
rem El lanzador principal prepara el entorno y mantiene visibles los errores.
"%~dp0iniciar_geforia.bat" --demo %*
