#!/bin/bash
cd /home/kavia/workspace/code-generation/culinary-companion-331171-331185/food_recipe_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

