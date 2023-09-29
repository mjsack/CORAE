from flask_wtf import FlaskForm
from wtforms import (FieldList, FileField, FormField, IntegerField,
                     PasswordField, SelectField, StringField, SubmitField)
from wtforms.validators import (DataRequired, EqualTo, Length, NumberRange,
                                ValidationError)

def EvenNumber(form, field):
    if form.bounding.data == 'bounded':
        if field.data is None:
            raise ValidationError('This field is required.')
        try:
            int_value = int(field.data)
        except ValueError:
            raise ValidationError('Value must be an integer.')

        if int_value % 2 != 0:
            raise ValidationError('Value must be an even number.')
        
class DeleteForm(FlaskForm):
    submit = SubmitField('Delete')
    
class ArchiveForm(FlaskForm):
    submit = SubmitField('Archive')
    
class DownloadForm(FlaskForm):
    submit = SubmitField('Download')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SettingsForm(FlaskForm):
    method = SelectField('Annotation Method', validators=[DataRequired()],
                         choices=[('CORAE', 'CORAE (Default)')], default='CORAE')
    capacity = IntegerField('Session Capacity', validators=[DataRequired(), NumberRange(min=1)])
    coupling = SelectField('Video Coupling', choices=[('coupled', 'Coupled (Default)'), ('decoupled', 'Decoupled')])
    ordering = SelectField('Video Sequencing', choices=[('random', 'Random (Default)'), ('ordered', 'Ordered')], default='random')
    bounding = SelectField('Bounding', validators=[DataRequired()],
                           choices=[('bounded', 'Bounded (Default)'),
                                    ('unbounded', 'Unbounded')], default='bounded')
    granularity = IntegerField('Granularity', validators=[EvenNumber, NumberRange(min=2)])
    axis = StringField('Primary Axis', validators=[DataRequired()])
    ceiling = StringField('Ceiling')
    floor = StringField('Floor')

class ProjectCreateForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = StringField('Project Description', validators=[DataRequired()])
    preset = SelectField('Preset', choices=[()], default='')
    settings = FormField(SettingsForm)
    submit = SubmitField('Save Project')
    
class ProjectJoinForm(FlaskForm):
    project_id = IntegerField('Project ID', validators=[DataRequired()])
    submit = SubmitField('Join Project')
    
class PresetCreateForm(FlaskForm):
    name = StringField('Preset Name', validators=[DataRequired()])
    description = StringField('Preset Description', validators=[DataRequired()])
    settings = FormField(SettingsForm)
    submit = SubmitField('Save Preset')

class SessionCreateForm(FlaskForm):
    participants = FieldList(StringField('Participant Name', validators=[DataRequired()]))
    videos = FieldList(FileField('Participant Video', validators=[DataRequired()]))
    general_videos = FileField('Session Videos', render_kw={"multiple": True})
    submit = SubmitField('Create Session')

    def __init__(self, capacity, *args, **kwargs):
        super(SessionCreateForm, self).__init__(*args, **kwargs)
        while len(self.participants) < capacity:
            self.participants.append_entry()