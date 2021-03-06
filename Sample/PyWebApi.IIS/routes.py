# -*- coding: utf-8 -*-
"""
    Routes for the sample PyWebApi Service.

    This module was originally shipped as an example code from https://github.com/DataBooster/PyWebApi, licensed under the MIT license.
    Anyone who obtains a copy of this code is welcome to modify it for any purpose, and holds all rights to the modified part only.
    The above license notice and permission notice shall be included in all copies or substantial portions of the Software.
"""

import os
from bottle import route, request, response, abort, error, make_default_app_wrapper
from pywebapi import RequestArguments, execute, cors, MediaTypeFormatterManager
from json_fmtr import JsonFormatter


_user_script_root = os.getenv("USER_SCRIPT_ROOT")
if not os.path.isabs(_user_script_root):
    _user_script_root = os.path.join(os.path.abspath(os.path.dirname(__file__)), _user_script_root)
_user_script_root = os.path.normpath(_user_script_root)

_server_debug = os.getenv("SERVER_DEBUG")

_mediatype_formatter_manager = MediaTypeFormatterManager(JsonFormatter())

def _get_user() -> str:
    return request.auth[0] if request.auth else None


def authorize_cors(func):
    def wrapped(*args, **kwargs):
        if cors.enable_cors(request, response):
            return None
        if not _get_user() and _server_debug != 'VisualStudio':
            abort(401, "The requested resource requires user authentication.")
        return func(*args, **kwargs)
    return wrapped



@route(path='/whoami', method=['GET', 'POST', 'OPTIONS'])
@authorize_cors
def who_am_i():
    return _get_user()


def check_permission(app_id:str, user_id:str, module_func:str) -> bool:
    #TODO: add your implementation of permission checks
    return True


@route(path='/pys/<app_id>/<module_func:path>', method=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@authorize_cors
def execute_module_level_function(app_id:str, module_func:str):
    user_name = _get_user()

    if check_permission(app_id, user_name, module_func):
        ra = RequestArguments(request)
        ra.override_value('actual_username', user_name)

        media_types = request.get_header('Accept', 'application/json')

        raw_result = execute(_user_script_root, module_func, ra.arguments)
        fmt_result = _mediatype_formatter_manager.respond_as(raw_result, media_types, response.headers.dict)

        return fmt_result
    else:
        abort(401, f"Current user ({repr(user_name)}) does not have permission to execute the requested {repr(module_func)}.")


@error(401)
@error(500)
def error_handler(err):
    try:
        if err.exception:
            err_msg = str(err.exception)
            resp_error = {"ExceptionType": type(err.exception).__name__}
        else:
            err_msg = err.body if err.body else str(err)
            resp_error = {}
        resp_error["ExceptionMessage"] = err_msg
        if err.traceback:
            resp_error["StackTrace"] = err.traceback

        media_types = request.get_header('Accept', 'application/json')
        return _mediatype_formatter_manager.respond_as(resp_error, media_types, response.headers.dict)
    except:
        default_error_handler = make_default_app_wrapper('default_error_handler')
        return default_error_handler(err)



__version__ = "0.1"
