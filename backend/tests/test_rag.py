"""Unit tests for RAG pipeline."""
import pytest
from unittest.mock import patch, MagicMock
from app.core.rag import retrieve_context


def test_retrieve_context_returns_string():
    with patch("app.core.rag._get_collection") as mock_col:
        mock_col.return_value.query.return_value = {
            "documents": [["Plan: Pro - $29/month. Features: Unlimited exports."]]
        }
        mock_col.return_value.count.return_value = 5
        result = retrieve_context("What is the Pro plan?")
        assert isinstance(result, str)
        assert "Pro" in result


def test_retrieve_context_handles_error():
    with patch("app.core.rag._get_collection") as mock_col:
        mock_col.return_value.query.side_effect = Exception("DB error")
        result = retrieve_context("test query")
        assert result == ""
