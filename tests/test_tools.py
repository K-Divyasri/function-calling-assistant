"""Tests for the four tools — tiny inputs, known answers."""

from __future__ import annotations

import pytest

from tool_agent.tools import do_math, get_weather, query_database, web_search


# -- do_math ------------------------------------------------------------- #

def test_do_math_basic():
    assert do_math("2 + 3") == "2 + 3 = 5"


def test_do_math_order_of_operations():
    assert do_math("2 + 3 * 4") == "2 + 3 * 4 = 14"


def test_do_math_parentheses():
    assert do_math("(3 + 4) * 5") == "(3 + 4) * 5 = 35"


def test_do_math_integer_result_has_no_trailing_zero():
    # 10 / 2 is 5.0 as a float; we present it as "5".
    assert do_math("10 / 2").endswith("= 5")


def test_do_math_rejects_code_injection():
    # The whole point of the ast approach: no eval, so this is refused, not run.
    out = do_math("__import__('os').system('echo hi')")
    assert out.startswith("Error")


def test_do_math_handles_divide_by_zero():
    assert "division by zero" in do_math("1 / 0")


# -- get_weather --------------------------------------------------------- #

def test_get_weather_known_city():
    out = get_weather("Paris")
    assert "Paris" in out and "15C" in out


def test_get_weather_unknown_city_is_friendly():
    out = get_weather("Atlantis")
    assert "Atlantis" in out and out.startswith("No offline weather")


# -- web_search ---------------------------------------------------------- #

def test_web_search_finds_relevant_doc():
    out = web_search("what is an embedding?")
    assert "embedding" in out.lower()


def test_web_search_strips_punctuation():
    # "RAG?" must still match the rag document despite the question mark.
    assert "retrieval" in web_search("what is RAG?").lower()


def test_web_search_no_results():
    assert "No results" in web_search("zzz qqq")


# -- query_database ------------------------------------------------------ #

def test_query_database_filters_by_department():
    out = query_database("employees", department="Engineering")
    assert "Ada Lovelace" in out


def test_query_database_two_filters():
    out = query_database("employees", department="Engineering", city="London")
    # 4 engineers are in London in the seed data.
    assert "Found 4 row" in out


def test_query_database_rejects_unknown_table():
    assert "unknown table" in query_database("salaries")


def test_query_database_rejects_bad_filter():
    # You can't filter employees by category — only department/city.
    assert "cannot filter" in query_database("employees", category="Hardware")
