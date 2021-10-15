""" This module holds tracecall, and thats about it. """
# pylint: disable=invalid-name, consider-using-f-string, unused-argument


def tracecall(enter_prefix="Calling :", enter_postfix="",
              exit_prefix="", exit_postfix=": DONE!", logger=None):
    """
    A decorator allowing us to log when a function is called, and when it
    returns.

    Parameters
    ----------
    enter_prefix : str
        The prefix to be prepended to the log message when then function is
        called.

    enter_postfix : str
        The postfix to be appended to the log message when the function is
        called.

    exit_prefix : str
        The prefix to be prepended to the log message when then function
        returns.

    exit_postfix : str
        The postfix to be appended to the log message when the function
        returns

    logger : str
        The logger to use, if it's not provided, it will use attempt to use
        whatever logging the calling object has.
    """
    def _tracecall(fn):
        def f(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = args[0].log
            msg = '{}{}{}'.format(enter_prefix, fn.__qualname__, enter_postfix)
            msg = msg.lstrip().rstrip()
            logger.debug(msg)
            result = fn(*args, **kwargs)
            logger.debug("{}{}{}".format(exit_prefix,
                                         fn.__qualname__,
                                         exit_postfix).lstrip().rstrip())
            return result
        return f
    return _tracecall
