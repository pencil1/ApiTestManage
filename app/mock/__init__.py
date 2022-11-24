from flask import Blueprint, current_app, request

mock = Blueprint('mock', __name__)

from . import mock_manage

