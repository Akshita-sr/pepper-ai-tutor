#
# main_brain_py3/services/document_processor.py
#
# Purpose: This class is solely responsible for the "Ingestion" part of a
# Retrieval-Augmented Generation (RAG) pipeline. Its job is to take a raw
# source document (in this case, a PDF file), load its content, and break it
# down into smaller, uniform text chunks. These chunks are then used to build
# the searchable AI memory (the vector store).
#

import logging
# imports a pdf reading class, A specialized class that can read PDF files and extract text.
from langchain_community.document_loaders import PyPDFLoader
# An intelligent text splitter that tries to keep related content together, Breaks large documents into smaller, meaningful chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Set up a logger for this module to provide useful output during execution, __name__: A special Python variable that contains the module's name ("document_processor")
# Purpose: Allows this class to create log messages that show where they came from
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    A class to handle the loading and splitting of documents, specifically PDFs,
    for use in a RAG pipeline.
    """

    def process_pdf(self, file_path: str):
        """
        Loads a PDF from the given file path and splits it into text chunks.
        This is the core method called by the setup script.

        Args:
            file_path (str): The path to the PDF file (e.g., "puzzles.pdf").

        Returns:
            list: A list of LangChain Document objects, where each object
                  represents a chunk of text from the original PDF.
        """
        logger.info(f"Starting to load and process PDF from: {file_path}")

        try:
            # Step 1: Load the PDF document using PyPDFLoader.
            # This library extracts the text content from the PDF file.
            # A class from LangChain that knows how to read PDFs, Creates a PyPDFLoader object with the specified file path
            loader = PyPDFLoader(file_path)
            documents = loader.load()  # load() is a method of the PyPDFLoader class, Actually reads the PDF and extracts all text, returns a  list of Document objects (one per page typically), Document objects: Special containers that hold text and metadata
            logger.info(
                f"Successfully loaded {len(documents)} page(s) from the PDF.")  # len(documents): Counts how many Document objects are in the list, Purpose: Confirms the loading worked and shows progress

            # Step 2: Split the loaded documents into smaller, manageable chunks.
            # We use RecursiveCharacterTextSplitter, which is good at keeping
            # related pieces of text together (like paragraphs).
            # - chunk_size: The maximum number of characters for each chunk here about 1000 characters.
            # - chunk_overlap: The number of characters from the end of one chunk
            #                  to overlap with the start of the next. This helps
            #                  maintain context between chunks.
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,  # Each chunk will share 200 characters with the next chunk
                length_function=len  # len: A built-in Python function that counts characters in a string
            )
            # Actually performs the splitting, split_documents() is a method of RecursiveCharacterTextSplitter, the input is a list of Document objects, the output is a new list of Document objects, each representing a smaller chunk of text
            splits = text_splitter.split_documents(documents)

            logger.info(
                f"Successfully split the document into {len(splits)} text chunks.")  # Reports how many chunks were created

            #  Sends the list of text chunks back to whoever called this method
            return splits

        # Handles the specific case where the PDF file doesn't exist
        except FileNotFoundError:
            logger.error(
                f"FATAL ERROR: The source file was not found at the specified path: {file_path}")
            # Re-raise the exception to stop the setup process immediately.
            raise

        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing the PDF: {e}")
            # Re-raise the exception for any other processing errors.
            raise


"""
Document Ingestion is the first step in a RAG pipeline:

Load: Read the raw document (PDF, text, etc.)
Split: Break it into smaller, manageable chunks
Process: Prepare chunks for embedding (converting to numbers)

Think of it like preparing a large book for an AI librarian - you need to break it into smaller, searchable sections.

"""
