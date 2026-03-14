# Quiz Maker 2 (QM2) - Interactive Terminal Quiz Application

[![PyPI version](https://badge.fury.io/py/qm2.svg)](https://badge.fury.io/py/qm2)
[![Python versions](https://img.shields.io/pypi/pyversions/qm2.svg)](https://pypi.org/project/qm2/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)](https://github.com/ahalvadzija/qm2)
[![CI/CD Pipeline](https://github.com/ahalvadzija/qm2/actions/workflows/pipeline.yml/badge.svg)](https://github.com/ahalvadzija/qm2/actions/workflows/pipeline.yml)

<figure>
  <img src="images/main-qm2.png" alt="Main Menu" />
  <figcaption><b>Figure 1:</b> The centralized dashboard of QM2, offering intuitive navigation through quiz modules, statistics, and system tools.</figcaption>
</figure>

**Quiz Maker 2 (QM2)** is a robust, interactive terminal-based quiz engine built with Python. Designed for developers and power users, it now features AI-powered quiz generation, allowing you to create comprehensive study materials in seconds using Google's Gemini AI. It features a modern UI, extensive import/export capabilities, and a high-performance core.

## Gameplay

<figure>
  <img src="images/gameplay-qm2.png" alt="Gameplay" />
  <figcaption><b>Figure 2:</b> Active quiz session featuring real-time timer, Rich-formatted output, and interactive choice selection.</figcaption>
</figure>

### Key Features

- **AI Quiz Generation**: Instantly generate quizzes on any topic using Google Gemini
- **4 Question Types**: Multiple Choice, True/False, Fill-in-the-blank, Matching
- **Timed Quiz Sessions**: Customizable timeout settings with real-time feedback
- **Flashcards Mode**: Study mode for reviewing questions without scoring
- **Score Tracking**: Comprehensive statistics and performance analytics
- **Category Management**: Organize questions into hierarchical categories
- **Import/Export**: Convert between CSV and JSON formats
- **Remote Import**: Download quiz files directly from URLs
- **Rich Terminal UI**: Beautiful, colored interface using Rich library
- **Performance Optimized**: Caching system for large question sets
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Flashcards Mode

<figure>
  <img src="images/flashcards-qm2.png" alt="Flashcards Mode" />
  <figcaption><b>Figure 3:</b> Flashcards study mode designed for stress-free learning, allowing users to flip through questions without scoring.</figcaption>
</figure>

## AI Generation Support

QM2 integrates with Google Gemini to automate quiz creation. You can generate professional-grade questions by simply providing a topic.

**Setup**

1. Get a free API key from Google AI Studio.
2. Export it to your environment:
    - Linux/macOS: export GEMINI_API_KEY='...'
    - Windows (CMD): set GEMINI_API_KEY=...
    - Windows (PowerShell): $env:GEMINI_API_KEY='...'

**AI Features**

- Smart Retries: Automatic fallback between models (Gemini 2.0 Flash -> 1.5 Flash -> 1.5 Pro) if one is unavailable.
- Rate Limit Handling: Built-in exponential backoff to handle API quotas gracefully.
- Topic-to-Quiz: Generates all 4 question types (including complex Matching) with high accuracy.

## Support

- **Email**: halvadzija.adnan@gmail.com
- **Issues**: [GitHub Issues](https://github.com/ahalvadzija/qm2/issues)

## Links

- **PyPI**: https://pypi.org/project/qm2/
- **GitHub**: https://github.com/ahalvadzija/qm2
- **Documentation**: https://ahalvadzija.github.io/qm2

---

**Created by**: [Adnan Halvadžija](https://github.com/ahalvadzija)

**⭐ If you find this project useful, please give it a star on GitHub!**

!!! love "Acknowledgments"
QM2 wouldn't be as beautiful or interactive without:

    * [Rich](https://github.com/Textualize/rich)
    * [Questionary](https://github.com/tmbo/questionary)
