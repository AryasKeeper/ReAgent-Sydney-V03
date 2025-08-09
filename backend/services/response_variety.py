"""Response variety templates for natural conversation"""
import random

GREETINGS = [
    "Agent Whisperer here, ready to help with Sydney property insights. ",
    "Hello! I'm Agent Whisperer, specializing in Sydney's real estate market. ",
    "Welcome! Agent Whisperer at your service for Sydney real estate. ",
    "Hi there! I'm Agent Whisperer, your Sydney property specialist. ",
    "Greetings! Agent Whisperer here to assist with Sydney real estate. "
]

SEARCH_INTROS = [
    "Let me search for properties matching your criteria...\n\n",
    "Searching for properties in your area of interest...\n\n",
    "Let me check what's available on the market...\n\n",
    "Looking for properties that match your requirements...\n\n",
    "Scanning the market for suitable properties...\n\n"
]

WEATHER_INTROS = [
    "Let me check the current conditions in Sydney...\n\n",
    "Here's the latest weather information for Sydney:\n\n",
    "Current Sydney weather update:\n\n"
]

FALLBACK_MESSAGES = [
    "I'm having difficulty accessing live listings right now. Let me provide some general market insights instead.",
    "Current property data is temporarily unavailable. Here's what I can tell you about the Sydney market:",
    "While I can't access specific listings at the moment, I can share market information:"
]

def get_greeting() -> str:
    """Get a random greeting message"""
    return random.choice(GREETINGS)

def get_search_intro() -> str:
    """Get a random search introduction"""
    return random.choice(SEARCH_INTROS)

def get_weather_intro() -> str:
    """Get a random weather introduction"""
    return random.choice(WEATHER_INTROS)

def get_fallback_message() -> str:
    """Get a random fallback message"""
    return random.choice(FALLBACK_MESSAGES)