import re

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:
    AnalyzerEngine = AnonymizerEngine = None

def redact_pii(text: str) -> str:
    """A readable baseline; use Presidio for production entity detection."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    return re.sub(r"\b\d{10}\b", "[PHONE]", text)

def redact_with_presidio(text: str) -> str:
    """Use Presidio when installed; keep the fallback easy to understand."""
    if AnalyzerEngine is None:
        return redact_pii(text)
    analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=text, language="en")
    return AnonymizerEngine().anonymize(text=text, analyzer_results=results).text

if __name__ == "__main__":
    print(redact_with_presidio("Contact analyst@example.com or 9876543210."))
    print("Optional next step: add presidio-analyzer and presidio-anonymizer from requirements.txt.")
