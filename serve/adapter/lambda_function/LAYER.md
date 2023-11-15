# Layer

You can get started with this code as a layer by using:

```
import serve.adapter.lambda_function


def app(http):
    http.response.body = {
        "Hello": "World"
    }


app_handler = serve.adapter.lambda_function.make_lambda_handler(app)
def lambda_handler(event, context):
    return app_handler(event, context)
```

The following scripts can help you create and publish layers:

* [layer_from_dirs.sh](layer_from_dirs.sh)
* [layer_from_requirements.sh](layer_from_requirements.sh)
* [publish_layer_zip.sh](publish_layer_zip.sh)

Have a look at the comment in each file for instructions.

