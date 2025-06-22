# from flask import Flask,redirect,url_for
from app import create_app
from sqlalchemy import create_engine

app= create_app()

if __name__=="__main__":
    app.run(port=3000, debug=True)
