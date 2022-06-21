import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def get_paginated_questions(request, questions, num_of_questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * num_of_questions
    end = start + num_of_questions

    questions = [question.format() for question in questions]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # Set up CORS. Allow '*' for origins.
    CORS(app, resources={'/': {'origins': '*'}})

    # Use the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        """ Set Access Control """

        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, PATCH, DELETE, OPTIONS')

        return response

    @app.route('/categories', methods=['GET'])
    def get_all_categories():
        
        try:
            categories = Category.query.all()

            categories_dictionary = {}
            for category in categories:
                categories_dictionary[category.id] = category.type

            return jsonify({
                'success': True,
                'categories': categories_dictionary
            }), 200
        except Exception:
            abort(500)

    @app.route('/questions', methods=['GET'])
    def get_questions():
       
        # get paginated questions and categories
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.order_by(Category.id).all()

        # Get paginated questions
        current_questions = get_paginated_questions(
            request, questions,
            QUESTIONS_PER_PAGE)

        # return 404 if there are no questions for the page number
        if (len(current_questions) == 0):
            abort(404)

        categories_dictionary = {}
        for category in categories:
            categories_dictionary[category.id] = category.type

        return jsonify({
            'success': True,
            'total_questions': len(questions),
            'categories': categories_dictionary,
            'current_category': [],
            'questions': current_questions
        }), 200

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.get(id)
            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'message': "Question successfully deleted"
            }), 200
        except Exception:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', '')
        new_answer = body.get('answer', '')
        new_category = body.get('category', '')
        new_difficulty = body.get('difficulty', '')
        search = body.get('searchTerm', '')

        try:
            if search:
                questions = Question.query.filter(
                    Question.question.ilike(f'%{search}%')
                ).all()

                current_questions = [question.format()
                                     for question in questions]
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(current_questions),
                })

            else:
                question = Question(
                    question=new_question,
                    answer=new_answer,
                    category=new_category,
                    difficulty=new_difficulty
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = get_paginated_questions(
                            request, selection, QUESTIONS_PER_PAGE)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })
        except Exception:
            abort(422)


    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def get_questions_by_category(id):

        category = Category.query.filter_by(id=id).one_or_none()

        if (category is None):
            abort(422)

        questions = Question.query.filter_by(category=id).all()

        paginated_questions = get_paginated_questions(
            request, questions,
            QUESTIONS_PER_PAGE)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(questions),
            'current_category': category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        try:
            data = request.get_json()
            previous_questions = data.get('previous_questions')
            quiz_category = data.get('quiz_category')

            if ((quiz_category is None) or (previous_questions is None)):
                abort(400)

            if (quiz_category['id'] == 0):
                questions = Question.query.all()
            else:
                questions = Question.query.filter_by(
                    category=quiz_category['id']).all()

            
            def get_random_question():
                return questions[random.randint(0, len(questions)-1)]

            next_question = get_random_question()

            found = True

            while found:
                if next_question.id in previous_questions:
                    next_question = get_random_question()
                else:
                    found = False

            return jsonify({
                'success': True,
                'question': next_question.format(),
            }), 200

        except Exception:
            abort(422)


    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad Request'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource Not Found'
        }), 404

    @app.errorhandler(422)
    def unprocesable_entity(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Not Processable'
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal Server Error'
        }), 500

    return app
    

