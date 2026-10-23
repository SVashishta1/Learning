# presidio_demo.py: the same job with Microsoft Presidio, an open-source PII toolkit used in production.
#
#   pip install -r requirements-optional.txt     (Presidio, spaCy and spaCy's small English model)
#   python presidio_demo.py
#
# Presidio combines patterns, checksums, context words and NER, like pii.py, with many more built-in
# recognisers (passports, national ids, US SSNs...). You can add your own, as we do for Northwind customer ids.
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from demo import EMAIL

TEXT = EMAIL + "Customer number: NWC-004471\n"


def build_analyzer():
    # Use spaCy's SMALL English model (Presidio's default is the large one, about 600 MB).
    nlp = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
    # A custom recogniser: Northwind customer numbers look like NWC-123456.
    analyzer.registry.add_recognizer(PatternRecognizer(
        supported_entity="NW_CUSTOMER_ID", patterns=[Pattern("nw customer id", r"\bNWC-\d{6}\b", 0.9)],
        context=["customer"]))
    return analyzer


def main():
    analyzer = build_analyzer()
    results = analyzer.analyze(text=TEXT, language="en",
                               entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "IBAN_CODE", "CREDIT_CARD",
                                         "IP_ADDRESS", "NW_CUSTOMER_ID"])
    print("Found:")
    for r in sorted(results, key=lambda r: r.start):
        print(f"   {r.entity_type:<15} {TEXT[r.start:r.end]!r:<42} score {r.score:.2f}")
    masked = AnonymizerEngine().anonymize(
        text=TEXT, analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
                   "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"})})
    print("\nMasked:\n" + masked.text)


if __name__ == "__main__":
    main()
