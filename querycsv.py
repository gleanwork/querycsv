"""
CSV processor for Glean questions and answers.

This module reads questions from a CSV file, processes them through the Glean API,
and writes the results back to a CSV file.
"""

import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

import gleanConstants as Constants
import gleanClientAPI as clientAPI

# Configure logging
logger = logging.getLogger('querycsv')

# read in environment variables
CONST = Constants.Constants()


def read_csv(file_name: str) -> List[Dict[str, str]]:
    """
    Read questions from a CSV file.

    Args:
        file_name: Path to the CSV file

    Returns:
        List of dictionaries containing question data
    """
    field_names = ["qid", "question", "answer", "research", "citations", "datetime"]
    questions = []

    try:
        with open(file_name, newline="", encoding="utf-8") as csvfile:
            doc = csv.DictReader(csvfile, fieldnames=field_names, delimiter=',')
            next(doc)  # Skip the header row

            if CONST.get_debug() or CONST.is_verbose():
                logger.info("Reading questions from CSV file: %s", file_name)

            for row in doc:
                questions.append(row)
                if CONST.get_debug() and CONST.is_verbose():
                    logger.setLevel(logging.DEBUG)
                    logger.debug("----------------")
                    for field in row:
                        value = row[field]
                        logger.debug("Field '%s': %s", field, value)
                    logger.setLevel(logging.INFO)

        return questions
    except FileNotFoundError:
        logger.error("File not found: %s", file_name)
        return []
    except Exception as e:
        logger.error("Error reading CSV file: %s", e)
        return []


def write_question_log(file_name: str, data: List[Dict[str, str]]) -> None:
    """
    Write question data to a CSV file.

    Args:
        file_name: Path to the output CSV file
        data: List of dictionaries containing question data
    """
    field_names = ["qid", "question", "answer", "research", "citations", "datetime"]

    try:
        with open(file_name, 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=',')

            # Write the header
            writer.writeheader()

            # Write the data
            for row in data:
                writer.writerow(row)
    except Exception as e:
        logger.error("Error writing to CSV file: %s", e)


def process_questions(questions: List[Dict[str, str]], log_file: str) -> None:
    """
    Process questions through the Glean API.

    Args:
        questions: List of question dictionaries
        log_file: Path to the output log file
    """
    processed_num = 0
    for question in questions:
        processed_num += 1

        if 'answer' in question and question['answer']:
            logger.info("Skipping question %s - already has an answer: %s", question['qid'], question['question'])
        else:
            logger.info("Processing question: %s", question['question'])
            question_response = clientAPI.getAnswer(question)

            # Check if there was an error
            if question_response.error:
                logger.error("Error processing question: %s", question_response.error)
                continue

            # Update the question with the response data
            if question_response.answer:
                question['answer'] = question_response.answer
                question['datetime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            if question_response.citations:
                question['citations'] = "\n".join(question_response.citations)

            if question_response.research:
                question['research'] = "\n".join(question_response.research)

            if not CONST.get_debug():
                logger.info("Syncing question log to: %s", log_file)
                write_question_log(log_file, questions)

        time.sleep(1)  # Pause execution for 1 second


def main() -> None:
    """Main function to run the CSV processor."""
    try:
        # Read questions from CSV
        question_data = read_csv(CONST.QUESTIONS_CSV)
        if not question_data:
            logger.error("No questions found or error reading CSV file. Exiting.")
            return

        # Generate log filename with timestamp
        now_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = CONST.QUESTIONS_CSV.replace('.csv', '') + f"_{now_time}.csv"
        if CONST.GLEAN_USER:
            log_file = log_file.replace('.csv', f"_{CONST.GLEAN_USER}.csv")

        # Process questions
        process_questions(question_data, log_file)

        logger.info("Processing complete.")

    except Exception as e:
        logger.error("An error occurred: %s", e)


if __name__ == "__main__":
    main()