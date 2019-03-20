from sfa_dash import create_app


app = create_app()
app.run(port=8080)
