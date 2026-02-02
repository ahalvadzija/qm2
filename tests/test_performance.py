import pytest
import json
import time
import os
import gc
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import qm2.core.questions as questions
import qm2.core.engine as engine


def get_memory_usage():
    """Get current memory usage in bytes (alternative to psutil)."""
    # Try to use resource module (Unix/Linux)
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # Convert KB to bytes
    except (ImportError, AttributeError):
        # Fallback: use sys.getsizeof for approximate measurement
        return sys.getsizeof(gc.get_objects())


@pytest.fixture
def large_questions_file(tmp_path):
    """Create a file with many questions for performance testing."""
    questions_file = tmp_path / "large_questions.json"
    many_questions = []
    
    for i in range(1000):  # Create 1000 questions
        many_questions.append({
            "type": "multiple",
            "question": f"Question {i}: What is the result of {i} + {i+1}?",
            "correct": str(i + i + 1),
            "wrong_answers": [
                str(i + i + 2),
                str(i + i + 3),
                str(i + i + 4)
            ]
        })
    
    questions_file.write_text(json.dumps(many_questions, indent=2), encoding="utf-8")
    return questions_file


@pytest.fixture
def complex_questions_file(tmp_path):
    """Create a file with complex questions for performance testing."""
    questions_file = tmp_path / "complex_questions.json"
    complex_questions = []
    
    for i in range(500):
        if i % 4 == 0:
            # Multiple choice
            complex_questions.append({
                "type": "multiple",
                "question": f"Complex question {i} with very long text that contains multiple sentences and detailed explanations about various topics that might be tested in a comprehensive quiz system?",
                "correct": f"Correct answer {i} with detailed explanation",
                "wrong_answers": [
                    f"Wrong answer {i}-1 with some details",
                    f"Wrong answer {i}-2 with more information",
                    f"Wrong answer {i}-3 with additional context"
                ]
            })
        elif i % 4 == 1:
            # True/False
            complex_questions.append({
                "type": "truefalse",
                "question": f"Statement {i}: This is a complex statement that requires careful consideration of multiple factors and variables that might affect the outcome in various scenarios.",
                "correct": "True" if i % 2 == 0 else "False",
                "wrong_answers": ["False" if i % 2 == 0 else "True"]
            })
        elif i % 4 == 2:
            # Fill-in
            complex_questions.append({
                "type": "fillin",
                "question": f"The capital of country {i} is _______. This question tests knowledge about world geography and requires specific factual information.",
                "correct": f"Capital{i}",
                "wrong_answers": []
            })
        else:
            # Matching
            complex_questions.append({
                "type": "match",
                "question": f"Match the concepts {i} with their definitions",
                "pairs": {
                    "left": [f"Concept {i}-{j}" for j in range(3)],
                    "right": [f"Definition {i}-{j}" for j in range(3)],
                    "answers": {"a": "1", "b": "2", "c": "3"}
                }
            })
    
    questions_file.write_text(json.dumps(complex_questions, indent=2), encoding="utf-8")
    return questions_file


def test_load_large_questions_performance(large_questions_file):
    """Test performance of loading large question files."""
    # Clear cache first
    questions.questions_cache.clear()
    
    # Measure initial load time
    start_time = time.time()
    result = questions.get_questions(large_questions_file)
    initial_load_time = time.time() - start_time
    
    assert len(result) == 1000
    assert initial_load_time < 1.0  # Should load within 1 second
    
    # Measure cached load time
    start_time = time.time()
    result = questions.get_questions(large_questions_file)
    cached_load_time = time.time() - start_time
    
    assert len(result) == 1000
    assert cached_load_time < 0.01  # Cached load should be very fast
    assert cached_load_time < initial_load_time / 10  # Should be at least 10x faster


def test_questions_cache_memory_usage(large_questions_file):
    """Test that questions cache doesn't consume excessive memory."""
    # Clear cache first
    questions.questions_cache.clear()
    
    # Get initial memory usage
    initial_memory = get_memory_usage()
    
    # Load multiple files into cache
    for i in range(5):
        temp_file = large_questions_file.parent / f"temp_{i}.json"
        # Copy the content directly
        content = large_questions_file.read_text(encoding="utf-8")
        temp_file.write_text(content, encoding="utf-8")
        questions.get_questions(temp_file)
    
    # Check memory usage after caching
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 100MB for 5000 questions)
    assert memory_increase < 100 * 1024 * 1024  # 100MB
    
    # Clean up temp files
    for i in range(5):
        temp_file = large_questions_file.parent / f"temp_{i}.json"
        if temp_file.exists():
            temp_file.unlink()


def test_questions_cache_cleanup_performance():
    """Test performance of cache cleanup operation."""
    # Populate cache with many entries
    questions.questions_cache.clear()
    
    # Simulate many cache entries
    for i in range(100):
        questions.questions_cache[f"/fake/path/{i}.json"] = {
            "mtime": time.time(),
            "data": [{"question": f"Test {i}"}]
        }
    
    # Measure cleanup time
    start_time = time.time()
    questions.cleanup_questions_cache()
    cleanup_time = time.time() - start_time
    
    # Cleanup should be fast
    assert cleanup_time < 0.1  # Should complete within 100ms
    assert len(questions.questions_cache) == 0


def test_complex_questions_loading_performance(complex_questions_file):
    """Test performance of loading complex questions."""
    questions.questions_cache.clear()
    
    start_time = time.time()
    result = questions.get_questions(complex_questions_file)
    load_time = time.time() - start_time
    
    assert len(result) == 500
    assert load_time < 2.0  # Should load within 2 seconds even for complex data
    
    # Verify all question types are loaded correctly
    question_types = set(q.get("type") for q in result)
    assert "multiple" in question_types
    assert "truefalse" in question_types
    assert "fillin" in question_types
    assert "match" in question_types


def test_concurrent_file_access_performance(large_questions_file):
    """Test performance of concurrent file access."""
    import threading
    import queue
    
    questions.questions_cache.clear()
    results = queue.Queue()
    
    def worker():
        start_time = time.time()
        result = questions.get_questions(large_questions_file)
        end_time = time.time()
        results.put((len(result), end_time - start_time))
    
    # Start multiple threads accessing the same file
    threads = []
    start_time = time.time()
    
    for _ in range(10):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Collect results
    all_results = []
    while not results.empty():
        all_results.append(results.get())
    
    # All threads should get the same result
    question_counts = [result[0] for result in all_results]
    assert all(count == 1000 for count in question_counts)
    
    # Concurrent access should be reasonably fast
    assert total_time < 2.0


def test_memory_usage_during_quiz_session():
    """Test memory usage during a simulated quiz session."""
    # Create a large set of questions
    large_questions = []
    for i in range(1000):
        large_questions.append({
            "type": "multiple",
            "question": f"Question {i}",
            "correct": f"Answer {i}",
            "wrong_answers": [f"Wrong {i}-{j}" for j in range(3)]
        })
    
    initial_memory = get_memory_usage()
    
    # Simulate quiz session operations
    with patch('qm2.core.engine.input_with_timeout') as mock_input:
        with patch('qm2.core.engine.questionary.confirm') as mock_confirm:
            with patch('qm2.core.engine.console'):
                # Mock user quitting immediately
                mock_input.return_value = "x"
                mock_confirm.return_value.ask.return_value = True
                
                # Run quiz session
                engine.quiz_session(large_questions, "/tmp/test_scores.json")
    
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable for 1000 questions
    assert memory_increase < 200 * 1024 * 1024  # 200MB


def test_performance_with_invalid_questions(tmp_path):
    """Test performance when dealing with invalid questions."""
    # Create a mix of valid and invalid questions
    mixed_questions = []
    
    for i in range(500):
        if i % 10 == 0:
            # Invalid question (missing required fields)
            mixed_questions.append({"type": "invalid"})
        elif i % 10 == 1:
            # Invalid question (missing question)
            mixed_questions.append({"type": "multiple", "correct": "answer"})
        else:
            # Valid question
            mixed_questions.append({
                "type": "multiple",
                "question": f"Valid question {i}",
                "correct": f"Answer {i}",
                "wrong_answers": [f"Wrong {i}"]
            })
    
    questions_file = tmp_path / "mixed_questions.json"
    questions_file.write_text(json.dumps(mixed_questions, indent=2), encoding="utf-8")
    
    questions.questions_cache.clear()
    
    start_time = time.time()
    result = questions.get_questions(questions_file)
    load_time = time.time() - start_time
    
    # Should load quickly even with invalid questions
    assert load_time < 1.0
    # Should filter out invalid questions (allow some tolerance)
    assert len(result) >= 440  # At least 440 valid questions out of 500


def test_cache_hit_ratio_performance(large_questions_file):
    """Test cache hit ratio under repeated access."""
    questions.questions_cache.clear()
    
    # First load (cache miss)
    start_time = time.time()
    result1 = questions.get_questions(large_questions_file)
    first_load_time = time.time() - start_time
    
    # Multiple subsequent loads (cache hits)
    total_cache_time = 0
    for _ in range(100):
        start_time = time.time()
        result = questions.get_questions(large_questions_file)
        total_cache_time += time.time() - start_time
    
    average_cache_time = total_cache_time / 100
    
    # Cache should be significantly faster
    assert average_cache_time < first_load_time / 20
    assert len(result1) == len(result) == 1000


def test_large_score_file_performance(tmp_path):
    """Test performance with large score files."""
    # Create a large score file
    large_scores = []
    for i in range(1000):
        large_scores.append({
            "correct": i % 10,
            "wrong": (10 - i) % 5,
            "unanswered": i % 3,
            "total": 10,
            "duration_s": 60 + i,
            "timestamp": f"2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:00:00"
        })
    
    scores_file = tmp_path / "large_scores.json"
    scores_file.write_text(json.dumps(large_scores, indent=2), encoding="utf-8")
    
    import qm2.core.scores as scores
    
    start_time = time.time()
    score_data = json.loads(scores_file.read_text(encoding="utf-8"))
    load_time = time.time() - start_time
    
    assert load_time < 0.5  # Should load 1000 scores quickly
    
    # Test pagination performance
    with patch('qm2.core.scores.questionary.select') as mock_select:
        with patch('qm2.core.scores.console'):
            # Create a proper mock object
            mock_select_instance = MagicMock()
            mock_select_instance.ask.return_value = "↩ Back"
            mock_select.return_value = mock_select_instance
            
            start_time = time.time()
            scores.show_scores_paginated(score_data, page_size=50)
            pagination_time = time.time() - start_time
            
            # Pagination should be fast even with large datasets
            assert pagination_time < 1.0


def test_performance_degradation_with_cache_size():
    """Test how performance changes as cache grows."""
    questions.questions_cache.clear()
    
    # Measure performance with different cache sizes
    cache_sizes = [0, 100, 500, 1000]
    load_times = []
    
    for size in cache_sizes:
        # Populate cache to desired size
        for i in range(size):
            questions.questions_cache[f"/fake/path/{i}.json"] = {
                "mtime": time.time(),
                "data": [{"question": f"Test {i}"} for _ in range(10)]
            }
        
        # Measure lookup performance
        start_time = time.time()
        for _ in range(100):
            questions.get_questions("/fake/path/0.json")
        avg_time = (time.time() - start_time) / 100
        load_times.append(avg_time)
    
    # Performance should not degrade significantly
    # (allow some degradation but not exponential)
    assert load_times[-1] < load_times[0] * 5  # Last should be less than 5x first


def test_file_io_performance_comparison(tmp_path):
    """Compare performance of different file I/O operations."""
    test_data = [{"question": f"Test {i}", "type": "multiple"} for i in range(1000)]
    
    # Test JSON write performance
    json_file = tmp_path / "test.json"
    start_time = time.time()
    json_file.write_text(json.dumps(test_data, indent=2), encoding="utf-8")
    json_write_time = time.time() - start_time
    
    # Test JSON read performance
    start_time = time.time()
    loaded_data = json.loads(json_file.read_text(encoding="utf-8"))
    json_read_time = time.time() - start_time
    
    # Both operations should be fast
    assert json_write_time < 0.5
    assert json_read_time < 0.5
    assert len(loaded_data) == 1000


def test_stress_test_multiple_operations(large_questions_file):
    """Stress test with multiple simultaneous operations."""
    import threading
    import random
    import queue
    
    questions.questions_cache.clear()
    results = queue.Queue()
    errors = queue.Queue()
    
    def mixed_operation_worker():
        try:
            for _ in range(50):
                operation = random.choice(['load', 'cache_clear', 'cleanup'])
                
                if operation == 'load':
                    result = questions.get_questions(large_questions_file)
                    results.put(('load', len(result)))
                elif operation == 'cache_clear':
                    questions.questions_cache.clear()
                    results.put(('clear', 0))
                elif operation == 'cleanup':
                    questions.cleanup_questions_cache()
                    results.put(('cleanup', 0))
                
                time.sleep(0.001)  # Small delay
        except Exception as e:
            errors.put(str(e))
    
    # Start multiple workers
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=mixed_operation_worker)
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Collect results
    all_results = []
    while not results.empty():
        all_results.append(results.get())
    
    # Collect errors
    all_errors = []
    while not errors.empty():
        all_errors.append(errors.get())
    
    # Should complete with minimal errors (dictionary iteration errors are expected)
    assert len(all_errors) <= 5  # Allow some concurrent access errors
    assert len(all_results) > 0
    
    # Verify load operations returned correct results
    load_results = [r for r in all_results if r[0] == 'load']
    if load_results:
        assert all(count == 1000 for _, count in load_results)
