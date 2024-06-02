
class APIError(Exception):
    """
    API error.

    Attributes:
        _code (str): The error code.
        _message (str): The error message.
    """
    code: str
    message: str

    def __init__(self, code: str, message: str) -> None:
        """
        Initializes a new instance of the AllDebridError class.

        Args:
            code (str): The error code.
            message (str): The error message.
        """
        super().__init__(f"{code} - {message}")
        self._code = code
        self._message = message

    @property
    def code(self) -> str:
        """
        The error code.

        Returns:
            str: The error code.
        """
        return self._code