from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from classifier import SubjectClassifier
load_dotenv()
class SmartRAGService():
    def __init__(self):
        print("Initializing Smart RAG Service...")
        self.embeddings = HuggingFaceEmbeddings(model_name= "sentence-transformers/paraphrase-MiniLM-L6-v2")

        self.vector_store = Chroma(
            collection_name= "loksewa_question",
            embedding_function= self.embeddings,
            persist_directory="./chroma.db"
        )
        self.llm = ChatGroq(
            temperature=0.7,
            model="llama-3.3-70b-versatile",
            api_key=os.getenv('GROQ_API_KE')
            )
        self.classifier = SubjectClassifier()

    def index_by_subject(self, file_path, subject):
        """
        1. Load PDF
        2. Split into chunks
        3. For each chunk:
           - Add metadata: {"subject": subject, "page": X}
        4. Add all chunks to ChromaDB
        5. Return chunk count
        """
        if os.path.exists(file_path):
            loader = PyPDFLoader(file_path)
        else: 
            print("No file path found")

        try:
            pdf_data = loader.load()
            print(f"Loaded {len(pdf_data)} pages....")

            splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200
            )
            chunks = splitter.split_documents(pdf_data)

            for chunk in chunks:
                chunk.metadata["subject"] = subject

            self.vector_store.add_documents(chunks)
            print(f"Splited into {len(chunks)} chunks...")
        except Exception as e:
            print("Error in index_by_subject(smart_rag): {e}")
        
    def smart_query(self, question):
        """1. Use classifier.predict(question)
           → Get predicted_subject + confidence
        
        2. If confidence < 0.6:
             Search ALL subjects (fallback)
           Else:
             Filter by predicted_subject
        
        3. Retrieve top 4 relevant chunks from ChromaDB
        
        4. Build prompt:
           "Based on this context: {chunks}
            Answer this {predicted_subject} question: {question}"
        
        5. Send to LLM
        
        6. Return:
           - answer
           - detected_subject
           - confidence
           - sources (chunks used)
        """
        try:
            predicted_data = self.classifier.predict(question)
            print(f"question: {question}, \nsubject: {predicted_data['subject']}, \nconfidencr:{predicted_data['confidence']}")
            
            if predicted_data['confidence'] < 0.6:
                retriver = self.vector_store.as_retriever(search_kwargs = 4)
            else:
                retriver = self.vector_store.as_retriever(search_kwargs = {"k": 4, "filter": {predicted_data['subject']}})
            
            relevant_doc = retriver.invoke(question)
            context = "\n\n" .join(doc.page_content for doc in relevant_doc)
            prompt = f"""
            You are a Teacher which has knowlegde all the knowledge on {predicted_data['subject']}
            Based on the follwing context : {context}
            answer this {predicted_data['subject']} question: {question}
            make sure you only return answer with less than 50 words"""

            messages = [
                {"role": "system", "content": "You are a Teacher which give answer to any question"},
                {"role": "user", "content": prompt}
            ]
            
            answer = self.llm.invoke(messages)
            sources = [
                {
                    "text": doc.page_content[:200] + "...",
                    "page": doc.metadata.get("page", 0),
                    "doc_id": doc.metadata.get("doc_id", "unknown"),
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in relevant_doc
            ]
            return {
                "answer": answer,
                "detected_subject": predicted_data['subject'],
                "confidence": predicted_data['confidence'],
                "sources" : sources
            }
        except Exception as e:
            print(f"Error in smart_query(smart_rag): {e}")
            return {

            }