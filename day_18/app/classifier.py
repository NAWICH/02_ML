'''classify sample question'''
import torch 
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
import sys
sys.path.append('../day_17')
from model import QuestionClassifier 
class SubjectClassifier():
    def __init__(self):
        self.encoder_classes = np.load('./models/label_encoder.npy')
        self.model = QuestionClassifier()
        self.model.load_state_dict(torch.load('./models/question_classifier.pth'))
        self.model.eval()

        self.embedder = HuggingFaceEmbeddings(model_name = "sentence-transformers/paraphrase-MiniLM-L6-v2")

    def predict(self,question_txt: str) -> dict:
        """
        Predict the subject of a Lok Sewa question
        1.convert question to embedding
        2.convert to pytorch tensor
        3.Pass through model
        4.get output logits
        5.Apply softmax to get probabilities
        6.use argmax to get predicted class
        7.Map index to subject name using label encoder
        8.return subject with confidence score
        """
        embedding = self.embedder.embed_query(question_txt)
        input_tensor = torch.FloatTensor([embedding])

        with torch.no_grad():
            output_logits = self.model(input_tensor)
            probabilities = torch.softmax(output_logits, dim=1)[0]

            predicted_idx = probabilities.argmax().item()
            predicted_subject = self.encoder_classes[predicted_idx]
            confidence = probabilities[predicted_idx].item()

            return {
                "question" : question_txt,
                "subject" : predicted_subject,
                "confidence": confidence
                }
        

classifier = SubjectClassifier()

test_questions = [
    "What is the capital of Nepal?",     # Should be GK
    "Calculate 15% of 200",              # Should be Math
    "Choose the correct article",        # Should be English
    "What is H2O?",                      # Should be Science
]

for q in test_questions:
    result = classifier.predict(q)
    print(f"{q[:30]:30} → {result['subject']:8} ({result['confidence']:.2%})")
