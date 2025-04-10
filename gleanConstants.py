import os
import sys
import getopt
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gleanConstants')

class Constants:
    """A Class for storing runtime configuration data"""

    # Defining here for IDE autocomplete 
    DEBUG = False
    GLEAN_AI_APP_ID = ""
    GLEAN_API_TOKEN = ""
    GLEAN_INSTANCE = ""
    GLEAN_USER = ""
    VERBOSE = False
    QUESTIONS_CSV = ""

    required_keys = [
        "DEBUG",
        "GLEAN_INSTANCE",
        "GLEAN_API_TOKEN",
        "QUESTIONS_CSV",
    ]

    other_keys = [
        "GLEAN_AI_APP_ID",
        "GLEAN_USER",
    ]

    true_vals = ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']

    def __init__(self) -> None:
        all_vars = True

        for required_key in self.required_keys:
            try:
                self.__dict__[required_key] = os.environ[required_key]
            except KeyError:
                all_vars = False
                logger.error(f"Required environment variable {required_key} not set")

        for other_key in self.other_keys:
            try:
                self.__dict__[other_key] = os.environ[other_key]
            except KeyError:
                pass

        if not all_vars:
            logger.error("Not all required environment variables are set. Exiting.")
            sys.exit()

        self.set_debug()

        argv = sys.argv[1:]
        try:
            opts, args = getopt.getopt(argv, "a:d:q:u:v", [
                "app-id=",
                "debug=",
                "questions-csv=",
                "user=",
                "verbose"
            ])

            for opt, arg in opts:
                if opt in ("-a", "--app-id"):
                    self.GLEAN_AI_APP_ID = f"{arg}"
                elif opt in ("-d", "--debug"):
                    self.set_debug(arg)
                elif opt in ("-q", "--questions-csv"):
                    self.QUESTIONS_CSV = f"{arg}"
                elif opt in ("-u", "--user"):
                    self.GLEAN_USER = f"{arg}"
                elif opt in ("-v", "--verbose"):
                    self.VERBOSE = True

        except getopt.GetoptError:
            logger.error('Usage: querycsv.py -v -d false -a <app-id> -q <questions-csv> -u <user>')
            pass

    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.VERBOSE

    def get_keys(self) -> Dict[str, Any]:
        """Get all keys in the Constants object."""
        return self.__dict__

    def get_debug(self) -> bool:
        """Get the debug mode status."""
        return self.DEBUG

    def set_debug(self, debug: Optional[str] = None) -> bool:
        """
        Set the debug mode status.
        
        Args:
            debug: Optional string value to set debug mode
            
        Returns:
            bool: The current debug mode status
        """
        if debug is not None:
            try:
                self.DEBUG = str(debug).lower() in self.true_vals
            except: 
                self.DEBUG = False
        else:
            try:
                self.DEBUG = os.environ["DEBUG"].lower() in self.true_vals
            except KeyError:
                self.DEBUG = False

        if self.DEBUG:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        return self.DEBUG