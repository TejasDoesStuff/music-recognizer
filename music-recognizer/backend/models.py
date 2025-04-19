import sqlalchemy
from db import metadata

songs = sqlalchemy.Table(
    "songs",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("title", sqlalchemy.String, nullable=False),
)

fingerprints = sqlalchemy.Table(
    "fingerprints",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("song_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("songs.id")),
    sqlalchemy.Column("hash", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("offset_time", sqlalchemy.Float, nullable=False),
)
