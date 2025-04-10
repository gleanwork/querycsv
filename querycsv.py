"""
CSV processor for Glean questions and answers.

This module reads questions from a CSV file, processes them through the Glean API,
and writes the results back to a CSV file.
"""

import csv
import time
import logging
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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


def process_questions(questions: List[Dict[str, str]], log_file: str) -> Tuple[List[float], int, int]:
    """
    Process questions through the Glean API.

    Args:
        questions: List of question dictionaries
        log_file: Path to the output log file

    Returns:
        Tuple containing:
        - List of API request times in seconds
        - Number of questions processed
        - Number of questions skipped
    """
    processed_num = 0
    skipped_num = 0
    api_times = []

    for question in questions:
        processed_num += 1

        if 'answer' in question and question['answer']:
            logger.info("Skipping question %s - already has an answer: %s", question['qid'], question['question'])
            skipped_num += 1
        else:
            logger.info("Processing question: %s", question['question'])
            start_time = time.time()
            question_response = clientAPI.getAnswer(question)
            end_time = time.time()
            request_time = end_time - start_time
            api_times.append(request_time)
            logger.info("API request completed in %.2f seconds", request_time)

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

    return api_times, processed_num, skipped_num


def display_timing_summary(api_times: List[float], processed_num: int, skipped_num: int) -> None:
    """
    Display a summary of API request timing statistics.

    Args:
        api_times: List of API request times in seconds
        processed_num: Total number of questions processed
        skipped_num: Number of questions skipped
    """
    if not api_times:
        logger.info("No API requests were made.")
        return

    avg_time = statistics.mean(api_times)
    median_time = statistics.median(api_times)
    min_time = min(api_times)
    max_time = max(api_times)
    
    logger.info("\nAPI Request Timing Summary:")
    logger.info("---------------------------")
    logger.info("Total questions: %d", processed_num)
    logger.info("Questions skipped: %d", skipped_num)
    logger.info("API requests made: %d", len(api_times))
    logger.info("Average request time: %.2f seconds", avg_time)
    logger.info("Median request time: %.2f seconds", median_time)
    logger.info("Minimum request time: %.2f seconds", min_time)
    logger.info("Maximum request time: %.2f seconds", max_time)
    logger.info("---------------------------")


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
        api_times, processed_num, skipped_num = process_questions(question_data, log_file)
        
        # Display timing summary
        display_timing_summary(api_times, processed_num, skipped_num)

        logger.info("Processing complete.")

    except Exception as e:
        logger.error("An error occurred: %s", e)


if __name__ == "__main__":
    main()