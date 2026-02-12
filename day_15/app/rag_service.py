"""RAG Service - Core document Q&A logic"""
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from chromadb.config import Settings
import os
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")

        self.embeddings = HuggingFaceBgeEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L6-v2")

        self.vector_store = Chroma(
            collection_name="pdf_collection", 
            embedding_function=self.embeddings,
            persist_directory="./chroma_db",
        )
        
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0
        )

    def index_document(self, file_path: str, doc_id: str) -> dict:
        try:
            """load PDF, split into chunks, create embeddings, store in vector DB"""
            #1.load
            print(f"Loading PDF: {file_path}")
            loader  = PyPDFLoader(file_path)
            pdf_data = loader.load()
            print(f"Loaded {len(pdf_data)} pages")

            #2.split
            splitter = RecursiveCharacterTextSplitter(
                chunk_size= 1000, 
                chunk_overlap=200
            )
            chunks = splitter.split_documents(pdf_data)
            print(f"Split into {len(chunks)} chunks")

            for chunk in chunks:
                chunk.metadata["doc_id"] = doc_id

            #3.store in vector DB
            ids = self.vector_store.add_documents(chunks)
            print(f"Stored {len(ids)} chunks in vector DB")

            return {
                "status": "success", 
                "chunks": len(ids), 
                "doc_id": doc_id,
                "pages": len(pdf_data)
                }
        
        except Exception as e:
            print(f"Error indexing document: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "doc_id": doc_id
            }
    def _format_docs(self, docs) -> str:
        """Format retrieved docs into single string"""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def query(self, question: str, doc_id: str = None) -> dict:
        """answer question using RAG"""
        try:
            search_kwargs = {"k": 4}
            if doc_id:
                search_kwargs["filter"] = {"doc_id": doc_id}
            
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )
            
            # Build prompt
            prompt = ChatPromptTemplate.from_template("""
                                                      You are a helpful assistant. Answer the question based ONLY on the context below.
                                                      If the answer is not in the context, say "I cannot find this in the document."
                                                      Context:{context}
                                                      Question: {question}
                                                      Answer:"""
                                                      )
            rag_chain = (
                {
                    "context": retriever | self._format_docs,
                    "question": RunnablePassthrough()
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )
            
            relevant_docs = retriever.invoke(question)
            
            answer = rag_chain.invoke(question)
            
            #
            sources = [
                {
                    "text": doc.page_content[:200] + "...",
                    "page": doc.metadata.get("page", 0),
                    "doc_id": doc.metadata.get("doc_id", "unknown"),
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in relevant_docs
            ]
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources
            }
        
        except Exception as e:
            print(f"Error querying: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "question": question
            }
    def get_documents(self) -> list:
        """Get list of indexed documents"""
        try:
            all_data = self.vector_store.get()

            if not all_data['metadatas']:
                return []
            
            seen  = set()
            documents = []

            for metadata in all_data['metadatas']:
                doc_id = metadata.get('doc_id')
                if doc_id and doc_id not in seen:
                    seen.add(doc_id)
                    documents.append({
                        "doc_id": doc_id,
                        "source": metadata.get('source', 'unknow'),
                        "pages": metadata.get('page', 0)
                    })
            
            return documents
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
        
    def delete_document(self, doc_id: str) -> bool:
        """Remove document from vector DB"""
        try:
            all_data = self.vector_store.get()

            ids_to_delete = [
                all_data['ids'][i]
                for i, metadata in enumerate(all_data['metadatas'])
                if metadata.get('doc_id') == doc_id
            ]

            if not ids_to_delete:
                print(f"No chunks found for doc_id: {doc_id}")
                return False
            
            self.vector_store.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} chunks for doc: {doc_id}")
            return True
        
        except Exception as e:
            print(f"Error in removing from vector db {e}")
            return False
        
    def get_stat(self) -> dict:
        """Get system statistics"""
        try:
            all_data = self.vector_store.get()
            total_chunks = len(all_data['ids'])

            documents= self.get_documents()

            return {
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "vector_store": "ChromaDB",
                "embedding_model": "paraphrase-MiniLM-L6-v2",
                "llm": "llama-3.1-8b-instant (Groq)"
            }
        except Exception as e:
            return {"error": str(e)}