"""Run the required demo questions through the agent and print full output,
including detected language, the English search query used internally, and the
Sources list, so real citations and multilingual behavior can be verified end
to end."""

from agent import ask, build_model

QUESTIONS = [
    "What is Section 3(p) of the Indian Patents Act?",
    "What is the Nagoya Protocol?",
    "Can I patent a traditional Ayurvedic formulation?",
    # Hindi translations of the same three questions
    "भारतीय पेटेंट अधिनियम की धारा 3(पी) क्या है?",
    "नागोया प्रोटोकॉल क्या है?",
    "क्या मैं किसी पारंपरिक आयुर्वेदिक फॉर्मूलेशन का पेटेंट करवा सकता हूँ?",
    # Mixed/Hinglish input
    "Ayurveda formulation patent kaise kare",
]


def main():
    model = build_model()
    for i, question in enumerate(QUESTIONS, 1):
        print("=" * 80)
        print(f"Q{i}: {question}")
        print("=" * 80)
        result = ask(question, model=model)
        print(f"[detected_language: {result['detected_language']}]")
        print(f"[english_query used for search: {result['english_query']}]")
        print()
        print(result["answer"])
        print()


if __name__ == "__main__":
    main()
