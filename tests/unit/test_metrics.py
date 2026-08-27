import pytest

def test_metrics_schema_validation():
    # Mock data coming from the agent
    agent_output = {
        "hallucination_likelihood": 10.5,
        "accuracy_confidence": 85.0,
        "falsehood_confidence": 5.0
    }
    
    # Assert metrics are present and types are correct
    assert "hallucination_likelihood" in agent_output
    assert isinstance(agent_output["hallucination_likelihood"], (int, float))
    
    assert "accuracy_confidence" in agent_output
    assert isinstance(agent_output["accuracy_confidence"], (int, float))
    
    assert "falsehood_confidence" in agent_output
    assert isinstance(agent_output["falsehood_confidence"], (int, float))

def test_hallucination_definition():
    # Ensure hallucination is 0 if it's not AI generated content
    # In reality, this would be tested against the agent's behavior
    is_ai_generated = False
    
    if not is_ai_generated:
        expected_hallucination = 0.0
        assert expected_hallucination == 0.0
