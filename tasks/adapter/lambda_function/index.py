import tasks.adapter.lambda_function
import app.tasks

lambda_handler = tasks.adapter.lambda_function.make_lambda_handler(app.tasks)
