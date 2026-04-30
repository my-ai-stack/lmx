"""Tests for task classifier."""

from lmx.classifier import classify_task, TaskType


def test_classify_summarization():
    assert classify_task("Summarize this article") == TaskType.SUMMARIZATION
    assert classify_task("Give me a tldr") == TaskType.SUMMARIZATION


def test_classify_code():
    assert classify_task("Debug this Python error") == TaskType.CODE
    assert classify_task("Write a function to sort lists") == TaskType.CODE


def test_classify_creative():
    assert classify_task("Write a blog post about AI") == TaskType.CREATIVE


def test_classify_batch():
    assert classify_task("Batch process 100 emails") == TaskType.BATCH
    assert classify_task("Bulk create 50 user accounts") == TaskType.BATCH


def test_code_flag():
    assert classify_task("anything", code=True) == TaskType.CODE


def test_batch_flag():
    assert classify_task("anything", batch=True) == TaskType.BATCH