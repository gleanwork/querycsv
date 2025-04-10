import json
import logging
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import gleanConstants as Constants

# Configure logging
logger = logging.getLogger('gleanClientAPI')

# read in environment variables
CONST = Constants.Constants()


@dataclass
class GleanResponse:
    """Structured response object for Glean API results."""
    answer: Optional[str] = None
    research: Optional[List[str]] = None
    citations: Optional[List[str]] = None
    error: Optional[str] = None


class GleanAPIError(Exception):
    """Custom exception for Glean API errors."""
    pass


def getAnswer(question: Dict[str, str]) -> GleanResponse:
    """
    Get an answer from the Glean API for a given question.
    
    Args:
        question (dict): A dictionary containing:
            - qid (str): Question ID
            - question (str): The question text
            - answer (str): The answer text
            - datetime (str): Timestamp
            
    Returns:
        GleanResponse: Structured response containing answer, research, and citations
        
    Raises:
        GleanAPIError: If there's an error with the API request or response
    """
    # Validate required fields
    required_fields = ['qid', 'question', 'answer', 'datetime']
    missing_fields = [field for field in required_fields if field not in question]
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        return GleanResponse(error=error_msg)

    apiEndpoint = "/rest/api/v1/chat"
    apiHost = f"{CONST.GLEAN_INSTANCE}-be.glean.com"
    url = f"https://{apiHost}{apiEndpoint}"

    # Requires the question and answer (combineAnswerText)
    payload = {
        "messages": [
            {
                "author": "USER",
                "messageType": "CONTENT",
                "fragments": [
                    {
                        "text": question['question']
                    }
                ]
            }
        ],
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CONST.GLEAN_API_TOKEN}"
    }

    if CONST.GLEAN_USER:
        headers['X-Scio-Actas'] = f"{CONST.GLEAN_USER}"

    if CONST.GLEAN_AI_APP_ID:
        payload['applicationId'] = f"{CONST.GLEAN_AI_APP_ID}"

    response = None
    answer_response = GleanResponse()

    if CONST.get_debug() or CONST.is_verbose():
        logger.debug("Making API request:")
        logger.debug("Host: %s", apiHost)
        logger.debug("Endpoint: %s", apiEndpoint)
        logger.debug("Question: %s", question['question'])
        logger.debug("Headers: %s", headers)
        logger.debug("Payload: %s", json.dumps(payload, indent=2))
    
    if not CONST.get_debug():
        try:
            if CONST.is_verbose():
                logger.info("Making chat API call")

            response = requests.request("POST", url, json=payload, headers=headers, timeout=30)

            if response.status_code > 200:
                error_msg = f"API error - status_code: {response.status_code}, response: {response.text}"
                logger.error(error_msg)
                answer_response.error = error_msg
                return answer_response
            
        except Exception as e:
            error_msg = f"Exception when posting to chat endpoint: {e}"
            logger.error(error_msg)
            answer_response.error = error_msg
            return answer_response
        
        if CONST.is_verbose():
            logger.debug("API Response:")
            logger.debug("Status code: %s", response.status_code)
            logger.debug("Response body: %s", json.dumps(json.loads(response.text), indent=2))

        try:
            parsed_answer = parseAnswer(response)
            if parsed_answer is not None:
                answer_response.answer = parsed_answer
                if CONST.is_verbose():
                    logger.debug("Parsed answer: %s", parsed_answer)

            parsed_research = parseResearch(response)
            if parsed_research is not None:
                answer_response.research = parsed_research
                if CONST.is_verbose():
                    logger.debug("Parsed research: %s", parsed_research)

            parsed_citations = parseCitations(response)
            if parsed_citations is not None:
                answer_response.citations = parsed_citations
                if CONST.is_verbose():
                    logger.debug("Parsed citations: %s", parsed_citations)

        except Exception as e:
            error_msg = f"Exception when parsing returned results: {e}"
            logger.error(error_msg)
            answer_response.error = error_msg

    return answer_response


def parseAnswer(response: requests.Response) -> Optional[str]:
    """
    Parse the answer from the API response.
    
    Args:
        response: The API response object
        
    Returns:
        str: The parsed answer text or None if not found
    """
    try:
        responseObj = json.loads(response.text)
        answer = None

        if 'messages' in responseObj:
            for message in responseObj['messages']:
                if 'fragments' in message:
                    for fragment in message['fragments']:
                        if 'text' in fragment:
                            answer = fragment['text']
                            logger.debug("Found answer: %s", answer)
        return answer
    except Exception as e:
        logger.error(f"Exception when parsing answer: {e}")
        return None


def parseCitations(response: requests.Response) -> Optional[List[str]]:
    """
    Extract citation URLs from the API response.
    
    Args:
        response: The API response object
        
    Returns:
        list: List of citation URLs or None if parsing fails
    """
    try:
        urls = []
        responseObj = json.loads(response.text)

        if 'messages' in responseObj:
            for message in responseObj['messages']:
                if 'citations' in message:
                    for citation in message['citations']:
                        if 'sourceDocument' in citation and 'url' in citation['sourceDocument']:
                            url = citation['sourceDocument']['url']
                            urls.append(url)

        return urls
    except Exception as e:
        logger.error("Exception when parsing citations: %s", e)
        return None


def parseResearch(response: requests.Response) -> Optional[List[str]]:
    """
    Extract research URLs from the API response.
    
    Args:
        response: The API response object
        
    Returns:
        list: List of research URLs or None if parsing fails
    """
    try:
        responseObj = json.loads(response.text)
        research_urls = []

        if 'messages' in responseObj:
            for message in responseObj['messages']:
                if 'fragments' in message:
                    reading_context = False
                    for fragment in message['fragments']:
                        # Check if this fragment indicates a "Reading" context
                        if 'text' in fragment and "**Reading:**" in fragment['text']:
                            reading_context = True

                        # If the reading context is identified, extract URLs from structuredResults
                        if reading_context and 'structuredResults' in fragment:
                            for result in fragment['structuredResults']:
                                if 'document' in result and 'url' in result['document']:
                                    research_urls.append(result['document']['url'])

        return research_urls
    except Exception as e:
        logger.error("Exception when parsing research: %s", e)
        return None