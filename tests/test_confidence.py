import os
import pytest
import json
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def patch_requests_post(monkeypatch):
    mock_post = MagicMock()
    monkeypatch.setattr("requests.post", mock_post)
    yield mock_post

# Patch transformers pipelines to avoid downloading models
@pytest.fixture(autouse=True)
def patch_pipelines(monkeypatch):
    mock_pipeline = MagicMock()
    
    mock_summarizer = MagicMock()
    mock_summarizer.return_value = [{"summary_text": "Mock summary"}]
    mock_classifier = MagicMock()
    mock_classifier.return_value = {"labels": ["bug"], "scores": [0.85]}
    
    monkeypatch.setattr("transformers.pipeline", lambda task, **kwargs: mock_summarizer if task == "summarization" else mock_classifier)
    yield

def test_confidence_score_not_zero(monkeypatch):
 
    monkeypatch.setenv("GITHUB_EVENT_PATH", "tests/sample_event.json")
    monkeypatch.setenv("GITHUB_REPOSITORY", "user/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "fake_token")
    
 
    sample_event = {
        "issue": {
            "number": 1,
            "title": "Sample Issue",
            "body": "This is a test body"
        }
    }
    
    with open("tests/sample_event.json", "w") as f:
        json.dump(sample_event, f)
    
    import action.main as main_module  


    assert main_module.score > 0, "Classifier score should not be zero"


    os.remove("tests/sample_event.json")
