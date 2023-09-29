import datetime
import os
from urllib.parse import urlparse

from flask import current_app
from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from werkzeug.security import check_password_hash, generate_password_hash

from .utils.extensions import db, login_manager

import uuid

participant_video_association = db.Table('participant_video_association',
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id'), primary_key=True),
    db.Column('video_id', db.Integer, db.ForeignKey('video.id'), primary_key=True),
    db.Column('order', db.Integer),
    db.Column('owner', db.Boolean, default=False)
)

class BaseModel(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    token = db.Column(db.String(128), unique=True, index=True)
    
    def generate_token(model):
        """
        Generate a unique token for a given  model.

        Parameters:
        - model (db.Model): The model for which the token needs to be generated.

        Returns:
        - str: A unique token.
        """
        MAX_ATTEMPTS = 100
        attempts = 0

        while attempts < MAX_ATTEMPTS:
            short_token = str(uuid.uuid4()).replace('-', '')[:7]
            if not model.query.filter_by(token=short_token).first():
                return short_token
            attempts += 1

        if attempts == MAX_ATTEMPTS:
            raise ValueError("Unable to generate a unique token after maximum attempts.")

class Researcher(UserMixin, BaseModel):
    __tablename__ = 'researcher'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', back_populates='researcher')
    presets = db.relationship('Preset', back_populates='researcher')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def tokenize(self):
        self.token = self.generate_token()
        
@login_manager.user_loader
def load_user(researcher_id):
    return Researcher.query.get(int(researcher_id))

class Settings(BaseModel):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(50), default="CORAE")
    capacity = db.Column(db.Integer, nullable=True, default=2)
    coupling = db.Column(db.String(50), default="coupled")
    ordering = db.Column(db.String(50), default="random")
    bounding = db.Column(db.String(50), nullable=True, default="bounded")
    granularity = db.Column(db.Integer, nullable=True, default=14)
    axis = db.Column(db.String(100), nullable=True, default="Social Distance")
    ceiling = db.Column(db.String(50), nullable=True, default="Approach")
    floor = db.Column(db.String(50), nullable=True, default="Withdrawal")

    project = db.relationship('Project', backref='settings')
    preset = db.relationship('Preset', backref='settings')
    
    @classmethod
    def default_values(cls):
        return {
            'method': "CORAE",
            'capacity': 2,
            'coupling': "coupled",
            'ordering': "random",
            'bounding': "bounded",
            'granularity': 14,
            'axis': "Social Distance",
            'ceiling': "Approach",
            'floor': "Withdrawal"
        }

    def to_dict(self):
        return {
            'method': self.method,
            'capacity': self.capacity,
            'coupling': self.coupling,
            'ordering': self.ordering,
            'bounding': self.bounding,
            'granularity': self.granularity,
            'axis': self.axis,
            'ceiling': self.ceiling,
            'floor': self.floor
        }

class Project(BaseModel):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    researcher = db.relationship('Researcher', back_populates='projects')
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    settings_id = db.Column(db.Integer, db.ForeignKey('settings.id'))
    sessions = db.relationship('Session', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def delete(self):
        for session in self.sessions:
            for participant in session.participants:
                for video in participant.videos:
                    video.delete_file()
        db.session.delete(self)
        db.session.commit()
    
    def apply_preset(self, preset, settings_form_data=None):
        new_settings = Settings()
        
        for attribute in Settings.__table__.columns:
            if hasattr(preset.settings, attribute.name) and hasattr(new_settings, attribute.name) and attribute.name != 'id':
                setattr(new_settings, attribute.name, getattr(preset.settings, attribute.name))
        
        if settings_form_data:
            for key, value in settings_form_data.items():
                if hasattr(new_settings, key):
                    setattr(new_settings, key, value)

        db.session.add(new_settings)
        db.session.commit()
        self.settings = new_settings
        
    def tokenize(self):
        self.token = self.generate_token()

class Preset(BaseModel):
    __tablename__ = 'preset'
    id = db.Column(db.Integer, primary_key=True)
    researcher_id = db.Column(db.Integer, db.ForeignKey('researcher.id'), nullable=False)
    researcher = db.relationship('Researcher', back_populates='presets')
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    settings_id = db.Column(db.Integer, db.ForeignKey('settings.id'))
    
    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'settings': self.settings,
        }

    def tokenize(self):
        self.token = self.generate_token()
        
class Session(BaseModel):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    description = db.Column(db.String(200))
    status = db.Column(db.Enum('active', 'archived', name='session_statuses'), default='active')
    participants = db.relationship('Participant', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def tokenize(self):
        self.token = self.generate_token()
        
    pass

class Participant(BaseModel):
    __tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    name = db.Column(db.String(100), nullable=False)
    has_accessed = db.Column(db.Boolean, nullable=False, default=False)
    last_accessed = db.Column(db.DateTime, nullable=True)
    has_submitted = db.Column(db.Boolean, nullable=False, default=False)
    
    videos = association_proxy('video_associations', 'video')
    video_ownership = association_proxy('video_associations', 'owner')
    video_order = association_proxy('video_associations', 'order')
    video_associations = db.relationship('ParticipantVideoAssociation', back_populates='participant', cascade='all, delete-orphan')

    
    def tokenize(self):
        self.token = self.generate_token()

    @staticmethod
    def verify_token(token):
        return Participant.query.filter_by(token=token).first()

    def join_session(self, session):
        if not self.is_joined_session(session):
            self.session = session

    def is_joined_session(self, session):
        return self.session_id == session.id

class Video(BaseModel):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=True)
    frame_rate = db.Column(db.Float, nullable=True)
    video_associations = db.relationship('ParticipantVideoAssociation', back_populates='video', cascade='all, delete-orphan')

    @property
    def display_path(self):
        if self.filepath.startswith('http'):
            return urlparse(self.filepath).path.split('/')[-1]
        return self.filepath

    @property
    def extension(self):
        return self.filepath.split('.')[-1]
    
    def tokenize(self):
        self.token = self.generate_token()
    
    def delete_file(self):
        try:
            os.remove(self.filepath)
        except Exception as e:
            current_app.logger.error(f"Error deleting video file {self.filepath}: {e}")
            
class Annotation(BaseModel):
    __tablename__ = 'annotation'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    timecode = db.Column(db.Float, nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    slider_position = db.Column(db.Float, nullable=False)

    participant = db.relationship('Participant', backref=db.backref('annotations', cascade='all, delete-orphan'))
    video = db.relationship('Video', backref=db.backref('annotations', cascade='all, delete-orphan'))

class ParticipantVideoAssociation(db.Model):
    __table__ = participant_video_association
    participant = db.relationship("Participant", back_populates="video_associations")
    video = db.relationship("Video", back_populates="video_associations")
    
    def __init__(self, video, participant=None, owner=False):
        self.video = video
        self.participant = participant
        self.owner = owner
        current_app.logger.debug(f"Associating video ID: {video.id} with participant ID: {participant.id if participant else 'None'}")
