from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class RegistroForm(FlaskForm):
    nombre_completo = StringField('Nombre completo', validators=[
        DataRequired(), Length(max=255)
    ])
    numero_telefonico = StringField('Número telefónico', validators=[
        DataRequired(), Regexp(r'^\d{10}$', message="Debe tener 10 dígitos")
    ])
    comunidad = StringField('Comunidad', validators=[
        DataRequired(), Length(max=100)
    ])
    municipio = StringField('Municipio', validators=[
        DataRequired(), Length(max=100)
    ])
    submit = SubmitField('Confirmar registro')
