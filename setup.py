from setuptools import setup, find_packages

setup(
    name="langbot",
    version="1.0.0",
    description="Telegram-бот для изучения английского языка",
    author="Nekrasov N.A.;Dmitriy O.A.",
    packages=find_packages(),
    # Основные зависимости для работы бота
    install_requires=[
        "pyTelegramBotAPI",
        "python-dotenv"
    ],
    # Дополнительные зависимости для сборки документации
    extras_require={

    },
    setup_requires=[
    ],
    python_requires=">=3.10",
    project_urls={
        "Documentation": "",
    },
)