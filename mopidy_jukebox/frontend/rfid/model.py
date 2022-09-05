from peewee import Model, DatabaseProxy, IntegerField, DateTimeField, BooleanField, TextField, FloatField, ForeignKeyField


database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


class Tag(BaseModel):
    uid = IntegerField(unique=True, primary_key=True)
    name = TextField(unique=True)
    registered = DateTimeField()
    enabled = BooleanField()
    media_uri = TextField()
    

class TagEncounter(BaseModel):
    uid = ForeignKeyField(Tag, backref='encounters')
    datetime = DateTimeField()
    duration = FloatField()
