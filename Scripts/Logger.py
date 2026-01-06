import logging

class Logger:

    """
    A simple logger class that uses Python's logging module to log messages.

    Class Attributes:
        None

    Class Methods:
        log(message, severity, file_name="default.log", to_console=False): Logs a message with the specified severity level.
    """

    @staticmethod
    def log(message, severity=logging.INFO, file_name="default.log", to_console=False):

        """
        Log a message with the specified severity level.

        Args:
            message (str)               : The message to be logged.
            severity (str)              : The severity level of the log message (debug, info, warning, error, critical).
            file_name (str, optional)   : The name of the log file. Default is "default.log".
            to_console (bool, optional) : If True, logs will be written to the console. Default is False.
                                          If False, logs will be written to the file specified by file_name.

        Returns                         : None
        """

        # Create a logger
        logger = logging.getLogger(__name__)
        
        # Set minimum logging level
        logger.setLevel(logging.DEBUG)
        
        # Decide where to log based on to_console parameter
        if to_console:
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHandler(file_name)

        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        
        # Log the message with the specified severity level
        logger.log(severity, message)
        
        # Remove handlers to avoid duplicate logs
        logger.removeHandler(handler)
            
        handler.close()

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)

# # usage
#     from Logger import *

    # Logger.log("This is an info message", logging.INFO)
    # Logger.log("This is a warning message", logging.WARNING, to_console=False)
    # Logger.log("This is an error message", logging.ERROR, file_name="..\Results\Time Tables\Agent_time_tables.log")
    # Logger.log("This is a debug message", logging.DEBUG, to_console=False)
