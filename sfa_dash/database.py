import datetime as dt


from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import JSONType


from sfa_dash.blueprints.auth0 import current_user


db = SQLAlchemy()


class OAuth(db.Model):
    @declared_attr
    def __tablename__(cls):
        return "oauth_token_storage"

    user = db.Column(db.String(24), primary_key=True)
    provider = db.Column(db.String(24), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow,
                           nullable=False)
    token = db.Column(JSONType, nullable=False)


session_storage = SQLAlchemyStorage(OAuth, db.session,
                                    user_required=True,
                                    user=current_user)
