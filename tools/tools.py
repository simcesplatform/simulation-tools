# -*- coding: utf-8 -*-

"""Common tools for the use of Omega and Simulation Manager."""

import datetime
import logging
import os
from typing import Dict, List, Tuple, Type, Union

SIMULATION_LOG_LEVEL = "SIMULATION_LOG_LEVEL"
SIMULATION_LOG_FILE = "SIMULATION_LOG_FILE"
SIMULATION_LOG_FORMAT = "SIMULATION_LOG_FORMAT"

EnvironmentVariableValue = Union[bool, int, float, str]
EnvironmentVariableType = Union[Type[bool], Type[int], Type[float], Type[str]]


class EnvironmentVariable:
    """Class for accessing and holding environment information."""

    def __init__(self, variable_name: str, variable_type: EnvironmentVariableType,
                 default_value: EnvironmentVariableValue = None):
        self.__variable_name = variable_name
        self.__variable_type = variable_type
        if default_value is None:
            self.__default_value = variable_type()
        else:
            self.__default_value = variable_type(default_value)

        self.__value_fetched = False
        self.__value = default_value

    @property
    def variable_name(self) -> str:
        """Return the variable name."""
        return self.__variable_name

    @property
    def variable_type(self) -> EnvironmentVariableType:
        """Returns the variable type."""
        return self.__variable_type

    @property
    def default_value(self) -> EnvironmentVariableValue:
        """Returns the default value for the variable."""
        return self.__default_value

    @property
    def value(self) -> EnvironmentVariableValue:
        """Returns the value of the environmental value.
           The value is only fetched from the environment at the first call."""
        if not self.__value_fetched:
            new_value = os.environ.get(self.variable_name)
            if new_value is None:
                self.__value = self.__default_value
            elif self.variable_type is bool:
                self.__value = new_value.lower() == "true"
            else:
                self.__value = self.variable_type(new_value)
            self.__value_fetched = True

        # This is added to allow pylance linter to recognize that self.__value cannot be None
        if self.__value is None:
            self.__value = self.default_value

        return self.__value

    def __str__(self) -> str:
        """Returns the string representation of the variable name and value."""
        return "{:s}: {:s}".format(self.variable_name, str(self.value))


EnvironmentVariableSetupType = Union[EnvironmentVariable, Tuple[str, EnvironmentVariableType],
                                     Tuple[str, EnvironmentVariableType, EnvironmentVariableValue]]


class EnvironmentVariables:
    """A class for accessing several environment variables."""

    def __init__(self, *variables: EnvironmentVariableSetupType):
        self.__variables = dict()
        for variable in variables:
            self.add_variable(variable)

    def add_variable(self, new_variable: EnvironmentVariableSetupType):
        """Adds new variable to the variable list.
           new_variable is either a EnvironmentVariable object or a tuple that can be used to create one."""
        if isinstance(new_variable, tuple):
            # The tuple parts handled explicitly to allow pylance linter to recognize the types.
            if len(new_variable) == 2:
                self.__variables[new_variable[0]] = EnvironmentVariable(new_variable[0], new_variable[1])
            elif len(new_variable) == 3:
                self.__variables[new_variable[0]] = EnvironmentVariable(
                    new_variable[0], new_variable[1], new_variable[2])
        elif isinstance(new_variable, EnvironmentVariable):
            self.__variables[new_variable.variable_name] = new_variable

    def get_variables(self) -> List[str]:
        """Returns a list of the registered environment variable names."""
        return list(self.__variables.keys())

    def get_value(self, variable_name: str) -> EnvironmentVariableValue:
        """Returns the value of the wanted environmental parameter.
           The value for each parameter is only fetched from the environment at the first call.
           If the given variable is not registered to the EnvironmentVariables instance, returns an empty string."""
        if variable_name in self.__variables:
            return self.__variables[variable_name].value

        LOGGER.info("Environment variable {:s} not registered.".format(variable_name))
        return str()


def load_environmental_variables(*env_variable_specifications: EnvironmentVariableSetupType) \
         -> Dict[str, EnvironmentVariableValue]:
    """Returns the realized environmental variable values as a dictionary."""
    env_variables = EnvironmentVariables(*env_variable_specifications)
    return {
        variable_name: env_variables.get_value(variable_name)
        for variable_name in env_variables.get_variables()
    }


COMMON_ENV_VARIABLES = load_environmental_variables(
    (SIMULATION_LOG_LEVEL, int, logging.DEBUG),
    (SIMULATION_LOG_FILE, str, "logfile.log"),
    (SIMULATION_LOG_FORMAT, str, " --- ".join([
        "%(asctime)s",
        "%(levelname)s",
        "%(name)s",
        "%(funcName)s",
        "%(message)s"]))
)


class FullLogger:
    """Logger object that also prints all the output."""
    MESSAGE_LEVEL = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL"
    }

    def __init__(self, logger_name: str, logger_level: Union[int, None] = None, stdout_output: bool = True):
        self.__logger = get_logger(logger_name, log_level=logger_level)
        self.__log_level = self.__logger.level
        self.__stdout_output = stdout_output

    def debug(self, message: str, *args):
        """Writes log message with DEBUG logging level."""
        if self.level <= logging.DEBUG:
            self.__logger.debug(message, *args)
            self.__print(logging.DEBUG, message, *args)

    def info(self, message: str, *args):
        """Writes log message with INFO logging level."""
        if self.level <= logging.INFO:
            self.__logger.info(message, *args)
            self.__print(logging.INFO, message, *args)

    def warning(self, message: str, *args):
        """Writes log message with WARNING logging level."""
        if self.level <= logging.WARNING:
            self.__logger.warning(message, *args)
            self.__print(logging.WARNING, message, *args)

    def error(self, message: str, *args):
        """Writes log message with ERROR logging level."""
        if self.level <= logging.ERROR:
            self.__logger.error(message, *args)
            self.__print(logging.ERROR, message, *args)

    def critical(self, message: str, *args):
        """Writes log message with CRITICAL logging level."""
        if self.level <= logging.CRITICAL:
            self.__logger.critical(message, *args)
            self.__print(logging.CRITICAL, message, *args)

    @property
    def level(self) -> int:
        """Returns the logging level of the logger."""
        return self.__logger.level

    @level.setter
    def level(self, log_level: int):
        """Sets the logging level of the logger to log_level."""
        self.__logger.setLevel(log_level)

    @property
    def logger_name(self) -> str:
        """Returns the logger name."""
        return self.__logger.name

    @property
    def logger(self):
        """Returns the Logger object."""
        return self.__logger

    def __print(self, message_level: int, message: str, *args):
        if self.__stdout_output and self.__log_level <= message_level:
            print(
                datetime.datetime.now().isoformat(),
                FullLogger.MESSAGE_LEVEL[message_level], ":", message % args,
                flush=True)


def get_logger(logger_name: str, log_level: Union[int, None] = None):
    """Returns a logger object."""
    new_logger = logging.getLogger(logger_name)
    if log_level is None:
        new_logger_level = COMMON_ENV_VARIABLES[SIMULATION_LOG_LEVEL]
    else:
        new_logger_level = log_level
    if isinstance(new_logger_level, int):
        new_logger.setLevel(new_logger_level)

    log_file_name = COMMON_ENV_VARIABLES[SIMULATION_LOG_FILE]
    if isinstance(log_file_name, str):
        log_file_handler = logging.FileHandler(log_file_name)
        log_file_handler.setFormatter(logging.Formatter(str(COMMON_ENV_VARIABLES[SIMULATION_LOG_FORMAT])))
        new_logger.addHandler(log_file_handler)

    return new_logger


LOGGER = FullLogger(__name__)


def handle_async_exception(event_loop, context):
    """Prints out any unhandled exceptions from async tasks."""
    # pylint: disable=unused-argument
    if isinstance(context, dict):
        exception = context.get("exception", None)
        if isinstance(exception, SystemExit):
            LOGGER.debug("SystemExit caught by async exception handler.")
    else:
        LOGGER.warning("Exception in async task: {:s}".format(str(context)))
