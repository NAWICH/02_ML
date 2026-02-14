"""
Question Generation Service for Lok Sewa Prep
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from app.database import (
    save_question,
    get_all_question_ids,
    get_user_attempted_question_ids
)

load_dotenv()

# System knowledge about Lok Sewa
LOKSEWA_SYSTEM_PROMPT = """
You are a Lok Sewa Aayog exam expert for Nepal.
You generate high-quality practice questions for government job aspirants.

Lok Sewa covers these subjects:
- GK: Nepal history, geography, constitution, government structure
- Nepali: Nepali grammar, comprehension, literature
- English: English grammar, vocabulary, reading comprehension
- Math: Basic arithmetic, algebra, reasoning, data interpretation
- Science: General science, environment, technology
- CurrentAffairs: Recent Nepal and world events

Question format rules:
- Questions must be factually accurate
- Wrong options must be plausible but clearly wrong
- Explanations must teach WHY the answer is correct
- Easy: basic recall, Medium: understanding, Hard: application/analysis
"""

class QuestionService:
    def __init__(self):
        print("Initializing Question Service...")

        # Embeddings model
        self.embeddings = HuggingFaceEmbeddings(  
            model_name="sentence-transformers/paraphrase-MiniLM-L6-v2"
        )

        # Vector store for past questions (duplicate detection)
        self.vector_store = Chroma(
            collection_name="loksewa_questions",
            embedding_function=self.embeddings,  
            persist_directory="./chroma_db"
        )

        # JSON parser
        self.parser = JsonOutputParser()

        # LLM
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0.7  # Slightly creative for varied questions
        )

        # Load and index past papers at startup
        self._index_past_papers()

        print("Question Service ready!")

    def _index_past_papers(self):
        """Load and index Lok Sewa past papers once at startup"""
        pdf_path = "./data/loksewa_questions.pdf"
        txt_path = "./data/loksewa_questions.txt"
        if os.path.exists(pdf_path):
            loader = PyPDFLoader(pdf_path)
        elif os.path.exists(txt_path):
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(txt_path, encoding='utf-8')  
        else:
            print("No study material found!")
            return

        try:
            pdf_data = loader.load()
            print(f"Loaded {len(pdf_data)} pages")

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = splitter.split_documents(pdf_data)
            print(f"Split into {len(chunks)} chunks")

            # ✅ Actually store in vector DB!
            self.vector_store.add_documents(chunks)
            print(f"Indexed {len(chunks)} chunks in vector DB")

        except Exception as e:
            print(f"Error loading past papers: {e}")
            print("Continuing with system prompt knowledge only")

    def _format_docs(self, docs) -> str:
        """Format retrieved docs into single string"""
        return "\n\n".join(doc.page_content for doc in docs)

    def generate_questions(
        self,
        subject: str = None,
        difficulty: str = None,
        count: int = 5,
        user_id: int = None
    ) -> list[dict]:
        """
        Generate fresh Lok Sewa practice questions

        Steps:
        1. Build query for retriever
        2. Retrieve relevant context from past papers
        3. Call LLM with specific prompt
        4. Parse JSON response
        5. Check for duplicates
        6. Save new questions to database
        7. Return questions WITHOUT correct answer
        """
        try:
            # 1. Build retrieval query
            query = f"{subject or 'general knowledge'} {difficulty or 'medium'} difficulty Lok Sewa questions"

            # 2. Get relevant context from past papers
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            )
            relevant_docs = retriever.invoke(query)
            context = self._format_docs(relevant_docs)

            # 3. Very specific prompt for structured output
            prompt_text = f"""
                {LOKSEWA_SYSTEM_PROMPT}

                Using the following context from past papers:
                {context}

                Generate EXACTLY {count} multiple choice questions.

                Requirements:
                - Subject: {subject or "any Lok Sewa subject"}
                - Difficulty: {difficulty or "medium"}
                - Each question must have exactly 4 options (A, B, C, D)
                - One correct answer, three plausible wrong answers
                - Clear explanation for why the correct answer is right

                You MUST return ONLY valid JSON in this exact format, nothing else:
                {{
                "questions": [
                    {{
                    "subject": "GK",
                    "difficulty": "medium",
                    "question_text": "What is the capital of Nepal?",
                    "option_a": "Pokhara",
                    "option_b": "Kathmandu",
                    "option_c": "Biratnagar",
                    "option_d": "Butwal",
                    "correct_option": "B",
                    "explanation": "Kathmandu is the capital and largest city of Nepal, serving as the political, cultural, and commercial center."
                    }}
                ]
                }}

                Return ONLY the JSON. No text before or after.
                """

            # 4. Call LLM
            messages = [
                {"role": "system", "content": "You are a JSON generator. Return only valid JSON."},
                {"role": "user", "content": prompt_text}
            ]

            response = self.llm.invoke(messages)

            # 5. Parse JSON response
            import json
            raw_text = response.content

            # Clean up response if needed
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            raw_questions = parsed.get("questions", [])

            # 6. Process each question
            final_questions = []
            for q in raw_questions:

                # Check for duplicates
                if self.check_duplicate(q['question_text']):
                    print(f"Skipping duplicate: {q['question_text'][:50]}...")
                    continue

                # Add unique ID and timestamp
                question_id = str(uuid.uuid4())
                q['id'] = question_id
                q['created_at'] = datetime.now().isoformat()

                # Save to database
                save_question(q)

                # Add to vector store for future duplicate detection
                from langchain_core.documents import Document
                self.vector_store.add_documents([
                    Document(
                        page_content=q['question_text'],
                        metadata={"question_id": question_id, "type": "generated_question"}
                    )
                ])

                # Return question WITHOUT correct answer
                final_questions.append({
                    "id": q['id'],
                    "subject": q['subject'],
                    "difficulty": q['difficulty'],
                    "question": q['question_text'],
                    "options": {
                        "A": q['option_a'],
                        "B": q['option_b'],
                        "C": q['option_c'],
                        "D": q['option_d']
                    }
                })

            return final_questions

        except Exception as e:
            print(f"Error generating questions: {e}")
            import traceback
            traceback.print_exc()
            return []

    def check_duplicate(self, question_text: str, threshold: float = 0.85) -> bool:
        """
        Check if question is too similar to existing ones.
        Returns True if duplicate, False if fresh.
        """
        try:
            results = self.vector_store.similarity_search_with_relevance_scores(
                question_text, k=1
            )

            if not results:
                return False

            doc, score = results[0]

            # Only check against generated questions, not past papers
            if doc.metadata.get("type") != "generated_question":
                return False

            print(f"Similarity score: {score:.4f}")
            return score >= threshold

        except Exception as e:
            print(f"Error checking duplicate: {e}")
            return False  # If error, assume not duplicate

    def get_explanation(self, question: dict, selected_option: str) -> dict:
        """
        Generate explanation for why answer is correct or incorrect.

        Args:
            question: Full question dict with correct_option
            selected_option: What user chose ("A", "B", "C", or "D")

        Returns:
            {
                "is_correct": bool,
                "correct": "B",
                "explanation": "...",
                "points_earned": int
            }
        """
        try:
            is_correct = selected_option == question['correct_option']

            # Map option letter to text
            option_map = {
                "A": question['option_a'],
                "B": question['option_b'],
                "C": question['option_c'],
                "D": question['option_d']
            }

            selected_text = option_map.get(selected_option, "Unknown")
            correct_text = option_map.get(question['correct_option'], "Unknown")

            # Build explanation prompt
            prompt_text = f"""
            Question: {question['question_text']}

            Options:
            A) {question['option_a']}
            B) {question['option_b']}
            C) {question['option_c']}
            D) {question['option_d']}

            Correct Answer: {question['correct_option']}) {correct_text}
            User Selected: {selected_option}) {selected_text}

            The existing explanation is: {question['explanation']}

            {"The user got this CORRECT! Reinforce why this answer is right." if is_correct else f"The user got this WRONG. They chose {selected_text} but the correct answer is {correct_text}."}

            Write a clear, educational explanation in 2-3 sentences. 
            Explain why the correct answer is right and why the wrong options are incorrect.
            """

            messages = [
                {"role": "system", "content": "You are a helpful Lok Sewa exam tutor. Give clear, educational explanations."},
                {"role": "user", "content": prompt_text}
            ]

            response = self.llm.invoke(messages)

            return {
                "is_correct": is_correct,
                "selected": selected_option,
                "correct": question['correct_option'],
                "explanation": response.content,
                "points_earned": 10 if is_correct else 0
            }

        except Exception as e:
            print(f"Error getting explanation: {e}")
            # Return basic explanation without LLM if error
            return {
                "is_correct": selected_option == question['correct_option'],
                "selected": selected_option,
                "correct": question['correct_option'],
                "explanation": question.get('explanation', 'No explanation available'),
                "points_earned": 10 if selected_option == question['correct_option'] else 0
            }