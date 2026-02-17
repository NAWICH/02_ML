import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, TensorDataset
from langchain_huggingface import HuggingFaceEmbeddings

from model import QuestionClassifier, SUBJECTS

LEARNING_RATE = 0.001
BATCH_SIZE =32
EPOCHS  = 30
DROPOUT = 0.3
MODEL_SAVE_PATH = "question_classifier.pth"
ENCODER_SAVE_PATH = "label_encoder.npy"

print("Loading dataser")
df = pd.read_csv("data/question_labeled.csv")
print(f"Total question: {len(df)}")
print("Distribution:")
print(df['subject'].value_counts())

questions = df['question'].tolist()
subjects = df['subject'].tolist()


#Encode Labels
encoder = LabelEncoder()
labels = encoder.fit_transform(subjects)

np.save(ENCODER_SAVE_PATH, encoder.classes_)
print(f"Label mapping : {dict(zip(encoder.classes_, range(len(encoder.classes_))))}")

#create Embedding
print("Creating embedding: ")
embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-MiniLM-L6-v2"
)

embeddings = np.array([embedder.embed_query(q) for q in questions])
print(f"embedding shape {embeddings.shape}")

#create dataset
X = torch.FloatTensor(embeddings)
y = torch.LongTensor(labels)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)

test_loader = DataLoader(TensorDataset(X_test, y_test), batch_size=BATCH_SIZE, shuffle=False)

print(f"\n Train : {len(X_train)} | Test : {len(X_test)}")

model = QuestionClassifier(drop_out_rate=DROPOUT)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
loss_fn = nn.CrossEntropyLoss()

print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")


#Training loop
print(f"Training for {EPOCHS} epochs")
best_test_accuracy = 0

train_losses = []
test_accuracies = []

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0
    train_correct = 0
    train_total = 0

    for batch_X, batch_y in train_loader:
        predictions= model(batch_X)
        loss = loss_fn(predictions, batch_y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        train_correct += (predictions.argmax(1) == batch_y).sum().item()
        train_total +=len(batch_y)

    #Evaluation phase
    model.eval()
    test_correct = 0
    test_total = 0

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            predictions = model(batch_X)
            test_correct += (predictions.argmax(1) == batch_y).sum().item()
            test_total += len(batch_y)

    avg_loss = train_loss/len(train_loader)
    train_acc = train_correct/train_total * 100
    test_acc = test_correct/test_total * 100

    train_losses.append(avg_loss)
    test_accuracies.append(train_acc)

    print(f"Epoch {epoch+1:2d}/{EPOCHS} | Loss: {avg_loss:.4f} | Train: {train_acc:.1f}% | Test: {test_acc:.1f}%")

    #save the best model
    if test_acc > best_test_accuracy:
        best_test_accuracy = test_acc
        torch.save(model.state_dict(), MODEL_SAVE_PATH)

print(f"Best test accuracy : {best_test_accuracy:.2f}")
print(f"Model saved to {MODEL_SAVE_PATH}")