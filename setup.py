from setuptools import setup, find_packages

setup(
    name="LangBot",
    version="1.0.0",
    description="Telegram-бот для изучения английского языка",
    author="Nekrasov N.A.; Ovchinnikov D.A.",
    packages=find_packages(),

    # Основные зависимости для работы бота
    install_requires=[
        "pyTelegramBotAPI",
        "python-dotenv"
    ],

    # Дополнительные зависимости для сборки документации
    extras_require={
        "docs": [
            "sphinx>=7.0",
            "sphinx-rtd-theme",
            "sphinx-copybutton",
            "myst-parser"
        ],
        "dev": [
            "sphinx>=7.0",
            "sphinx-rtd-theme",
            "sphinx-copybutton",
            "myst-parser",
            "pytest"
        ]
    },

    python_requires=">=3.12",

    project_urls={
        "Documentation": "",
        "Source": "https://github.com/nnekrasov1/LangBot"
    },
)