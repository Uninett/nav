
class GeneralError(Exception):
    "General error"
    def __str__(self):
        args = Exception.__str__(self) # Get our arguments
        return self.__doc__ + ': ' + args

class ConfigurationError(GeneralError):
    "Configuration error"

class BasepathError(ConfigurationError):
    "Configuration error, unknown basepath"

class RedirectError(GeneralError):
    "Need to redirect"
