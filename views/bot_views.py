from flask import Blueprint, render_template

pdf = Blueprint('PDF Chat Bot', __name__, url_prefix='/pdf')
chat = Blueprint('DCU Chat Bot', __name__, url_prefix='/chat')

@pdf.route('/hello')
def hello_pybo():
    return '''hello / pdf'''

@chat.route('/hello')
def hello_pybo():
    return '''hello / chat'''
