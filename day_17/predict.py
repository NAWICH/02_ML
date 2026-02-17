"""
Use trained model to predict subject of a question
"""

import torch
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from model import QuestionClassifier

# Load model and resources
def load_model():
    encoder_classes = np.load("label_encoder.npy", allow_pickle=True)
    
    model = QuestionClassifier()
    model.load_state_dict(torch.load("question_classifier.pth"))
    model.eval()
    
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-MiniLM-L6-v2"
    )
    
    return model, embedder, encoder_classes

model, embedder, encoder_classes = load_model()

def predict_subject(question_text: str) -> dict:
    """
    Predict the subject of a Lok Sewa question
    
    Returns:
        {
            "question": "...",
            "subject": "GK",
            "confidence": 0.92,
            "all_probabilities": {"GK": 0.92, "Math": 0.03, ...}
        }
    """
    with torch.no_grad():
        # Convert to embedding
        embedding = embedder.embed_query(question_text)
        input_tensor = torch.FloatTensor([embedding])
        
        # Get predictions
        logits = model(input_tensor)
        
        # Convert to probabilities
        probabilities = torch.softmax(logits, dim=1)[0]
        
        # Get top prediction
        predicted_idx = probabilities.argmax().item()
        predicted_subject = encoder_classes[predicted_idx]
        confidence = probabilities[predicted_idx].item()
        
        # All probabilities
        all_probs = {
            encoder_classes[i]: round(probabilities[i].item(), 4)
            for i in range(len(encoder_classes))
        }
        
        return {
            "question": question_text,
            "subject": predicted_subject,
            "confidence": round(confidence, 4),
            "all_probabilities": all_probs
        }

# Test it
if __name__ == "__main__":
    test_questions = [
        "What is the capital of Nepal?",
        "Calculate 25% of 400",
        "नेपालीमा स्वर संख्या कति छ?",
        "Choose the correct article: ___ apple",
        "What is the chemical formula of water?"
    ]
    
    print("Testing Question Classifier:")
    print("=" * 50)
    for q in test_questions:
        result = predict_subject(q)
        print(f"Q: {q[:50]}")
        print(f"→ {result['subject']} ({result['confidence']*100:.1f}% confident)")
        print()