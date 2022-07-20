import logging

# ! implement email sending on error
def handle_exception() -> None:
    # ! gmail no longer supports app login with username and password
    # ! as such, can't use google to send emails
    logging.exception("")
