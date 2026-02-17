"""
Generate labeled training data using Day 16 question service
"""
import json
import csv
import sys
sys.path.append('../day_16')
from app.question_service import QuestionService # type: ignore

def generate_training_data():
    service = QuestionService()

    subjects = ['Gk', 'Math', 'Nepali', 'English', 'Science']
    difficulities = ['easy', 'medium', 'hard']

    all_questions = []

    for subject in subjects:
        for diffculty in difficulities:
            print(f"Generating {subject} {diffculty} questions...")
            questions = service.generate_questions(subject=subject, difficulty=diffculty, count = 20)

            for q in questions:
                all_questions.append({"question": q['question'], "subject": subject})

    #save to csv
    with open('data/question_labeled.csv','w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['question', 'subject'])
        writer.writeheader()
        writer.writerows(all_questions)

    print(f"Saved {len(all_questions)} questions!")
    print("Distribution:")
    from collections import Counter
    counts = Counter(q['subject'] for q in all_questions)
    for subject, count in counts.items():
        print(f"  {subject}: {count}")

if __name__ == "__main__":
    generate_training_data()