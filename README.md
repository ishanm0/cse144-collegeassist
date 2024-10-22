# college assist

![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat)
![Python Version](https://img.shields.io/badge/python-3.11-blue)

## Description

## Backend

### 1. **Install Poetry**

1. Install Poetry if you haven't already:

    ```bash
    pip install poetry
    ```

2. Install the project dependencies:

    ```bash
    poetry install --no-root
    ```

3. Run the application:

    ```bash
    poetry run python app.py
    ```

### 2. **Set Up Pre-commit Hooks**

This project uses [pre-commit](https://pre-commit.com/) to enforce coding standards and run checks before committing code. To install pre-commit hooks:

```bash
pre-commit install
```

After this, every time you make a commit, the hooks will run automatically to ensure code quality.
