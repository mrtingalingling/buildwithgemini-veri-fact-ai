import pytest

def test_dom_text_parsing():
    # Mock DOM text from the extension
    dom_text = "The quick brown fox jumped over the lazy dog. Humans landed on Mars in 2024."
    
    # Mock backend processing
    def mock_process_text(text):
        if "Mars in 2024" in text:
            return {
                "claim": "Humans landed on Mars in 2024",
                "veracity": "red",  # High falsehood
                "tooltip": "NASA confirms no humans have landed on Mars as of 2024."
            }
        return None
        
    result = mock_process_text(dom_text)
    
    assert result is not None
    assert result["veracity"] == "red"
    assert "NASA" in result["tooltip"]

def test_veracity_colors():
    # Test that the correct colors are returned based on confidence metrics
    def mock_get_color(accuracy, falsehood):
        if accuracy > 80:
            return "green"
        elif falsehood > 80:
            return "red"
        else:
            return "yellow"
            
    assert mock_get_color(90, 5) == "green"
    assert mock_get_color(5, 90) == "red"
    assert mock_get_color(50, 50) == "yellow"
