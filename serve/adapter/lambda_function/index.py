import serve.adapter.lambda_function

# Make sure this is after to set up the environment correctly
import app.app

lambda_handler = serve.adapter.lambda_function.make_lambda_handler(app.app.app)
