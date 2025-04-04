import os
import tempfile
from unittest.mock import patch
import importlib.util
import pytest

import plomp


def import_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def examples_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


@pytest.fixture
def temp_html_file():
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
        yield temp_file.name
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


@pytest.fixture(autouse=True)
def patch_write_html():
    """Automatically patch plomp.write_html for all tests in this module."""
    with patch("plomp.write_html", return_value=None) as mock:
        yield mock


def test_basic_example_functions(examples_dir, temp_html_file):
    basic_example_path = os.path.join(examples_dir, "basic_example.py")
    basic_example = import_module_from_file(basic_example_path, "basic_example")

    response = basic_example.simulate_llm_response("Hello, world!")
    assert "Hello, world" in response

    with patch.object(
        basic_example,
        "simulate_llm_response",
        return_value="Paris is the capital of France",
    ):
        basic_example.example_manual_recording()

    with patch.object(basic_example, "simulate_llm_response") as mock_sim:
        mock_sim.side_effect = [
            "The top attractions are Eiffel Tower, Louvre, Notre Dame",
            "Day 1: Visit Eiffel Tower. Day 2: Explore Louvre",
        ]
        basic_example.example_decorator_recording()

    test_buffer = plomp.buffer(key="test_basic_responses")
    with patch("plomp.buffer", return_value=test_buffer):
        with patch.object(
            basic_example,
            "simulate_llm_response",
            return_value="Paris is the capital of France",
        ):
            basic_example.example_manual_recording()

        events = [item for item in test_buffer if item.type_.value == "event"]
        for event in events:
            assert "response_excerpt" in event.event.payload


def test_query_example_functions(examples_dir, temp_html_file):
    query_example_path = os.path.join(examples_dir, "query_example.py")
    query_example = import_module_from_file(query_example_path, "query_example")

    response = query_example.simulate_llm_response("Test query")
    assert "Test query" in response

    test_buffer = plomp.buffer(key="test_query_example")

    with patch("random.uniform", return_value=1.0):
        with patch("plomp.buffer", return_value=test_buffer):
            with patch.object(query_example, "simulate_llm_response") as mock_sim:
                mock_sim.side_effect = [
                    "London weather is cloudy with a chance of rain",
                    "New York weather is sunny and warm today",
                    "Quantum computing uses quantum bits called qubits",
                    "The weather data shows consistent patterns",
                ]

                query_example.record_sample_data()
                query_example.run_query_examples()

    assert len(test_buffer) > 0


def test_end_to_end_examples(examples_dir, temp_html_file):
    basic_example_path = os.path.join(examples_dir, "basic_example.py")
    query_example_path = os.path.join(examples_dir, "query_example.py")

    basic_example = import_module_from_file(basic_example_path, "basic_example")
    query_example = import_module_from_file(query_example_path, "query_example")

    test_buffer = plomp.buffer(key="test_end_to_end")

    with patch("plomp.buffer", return_value=test_buffer):
        with patch.object(basic_example, "simulate_llm_response") as mock_basic_sim:
            mock_basic_sim.side_effect = [
                "Paris is the capital of France",
                "The top attractions are Eiffel Tower, Louvre, Notre Dame",
                "Day 1: Visit Eiffel Tower. Day 2: Explore Louvre",
            ]
            basic_example.example_manual_recording()
            basic_example.example_decorator_recording()

        with patch("random.uniform", return_value=1.0):
            with patch.object(query_example, "simulate_llm_response") as mock_query_sim:
                mock_query_sim.side_effect = [
                    "London weather is cloudy with a chance of rain",
                    "New York weather is sunny and warm today",
                    "Quantum computing uses quantum bits called qubits",
                    "The weather data shows consistent patterns",
                ]
                query_example.record_sample_data()
                query_example.run_query_examples()
